#!/usr/bin/env python

import os, sys
import json
import subprocess
import multiprocessing, time, datetime
from optparse import OptionParser
from CMSSWUtility.job_submitor.DASClient import DASClient

def Option_Parser(argv):

    usage='usage: %prog [options] arg\n'
    parser = OptionParser(usage=usage)

    parser.add_option('-d', '--dataset',
            type='str', dest='dataset', default='/ZMM*/*/MINIAOD',
            help='input your dataset like /ZMM*/*/MINIAOD from DAS'
            )
    parser.add_option('--PileupCfi',
            type='str', dest='PileupCfi', default='flashgg.MetaData.PU_MixFiles_2017_miniaodv2_310.mix_2017MC_VBFHToGG_M125_13TeV_amcatnlo_pythia8',
            help='input pile up cfi file based on CMSSW/src'
            )
    parser.add_option('--minbiasPileup',
            type='str', dest='minBiasPileup', default='MyDataPileupHistogram.root',
            help='tag output MC samples'
            )
    parser.add_option('-n', '--ncore',
            type='int', dest='ncore', default = multiprocessing.cpu_count(),
            help='input how many cpu you will use (Max has to be the machine ncore)'
            )
    parser.add_option('-o', '--output',
            type='str', dest='output', default = 'fileinfo2017.json',
            help='create a file with MC info recorded if the file is not exist, but exist, the progrem will update the file if this info is not in this file'
            )
    parser.add_option('--force',
            action='store_true', dest='force',
            help='force to get events info even if the mc you specify is exist in outfile'
            )


    (options, args) = parser.parse_args(argv)
    return options

def GetRealGenNumber (file, puweight, q):

    import ROOT
    from DataFormats.FWLite import Events, Handle

    filelink = ''
    try: #Avoid error link
        remotes = ['root://eoscms.cern.ch//eos/cms', 'root://xrootd-cms.infn.it/', 'root://cmsxrootd.fnal.gov/', 'root://cms-xrd-global.cern.ch/']

        for re in remotes:
            filelink = re + file
            fin = ROOT.TFile.Open(filelink)
            if fin and not fin.IsZombie():
                break
        if not fin or fin.IsZombie():
            q.put( [0, file] )
            sys.exit(0)
    except:
        q.put( [0, file] )
        sys.exit(0)

    events = Events (filelink)

    # create handle outside of loop
    pileup_handle, pileup_label  = Handle('std::vector<PileupSummaryInfo>'), 'slimmedAddPileupInfo'
    gen_handle, gen_label        = Handle('GenEventInfoProduct'), 'generator'

    ROOT.gROOT.SetBatch()        # don't pop up canvases
    nevent = 0
    sumweight = 0
    for event in events:
        # use getByLabel, just like in cmsRun
        event.getByLabel( pileup_label, pileup_handle )
        event.getByLabel( gen_label, gen_handle )

        nip = -1
        for pu in pileup_handle.product():
            if pu.getBunchCrossing() == 0:
                nip = pu.getTrueNumInteractions()
                break
        nevent += 1
        sumweight += ( gen_handle.product().weight() * puweight[int(nip)] if nip > 0 and nip < len(puweight) else 0 )
    q.put( [nevent, sumweight, ''] )

class ParallelCalculator():

    def __init__ (self, target, filelist, puweight, maxproc):
        self.target        = target
        self.filelist      = filelist
        self.puweight      = puweight
        self.maxproc       = maxproc
        self.queue         = multiprocessing.Queue()

    def prepare_processes (self):
        p = list()
        for file in self.filelist:
            p.append( multiprocessing.Process(target = self.target,
                                                args = (file, self.puweight, self.queue, )) )

        self.p = p

    def start (self):
        self.prepare_processes()

        njobs = len(self.filelist)
        print 'Need %s jobs' % njobs

        iproc = 0
        pend_jobs = njobs
        tmp_index = -1

        init_time = datetime.datetime.now()

        while len(multiprocessing.active_children()) != 0 or pend_jobs != 0 :

            if len(multiprocessing.active_children()) is not tmp_index:
                run_jobs = len(multiprocessing.active_children())
                finish_jobs = njobs - pend_jobs - run_jobs
                delta_time = (datetime.datetime.now() - init_time).total_seconds()

                minutes = int(delta_time / 60)
                seconds = delta_time - minutes * 60

                print 'Pending : %d, Running : %d, Finished : %d, [ time : %dm %ds ]' % ( pend_jobs,
                                                                                   run_jobs,
                                                                                   finish_jobs,
                                                                                   minutes,
                                                                                   seconds )
                tmp_index = run_jobs

            if len(multiprocessing.active_children()) < self.maxproc and iproc < njobs:
                submit_jobs = min( njobs - iproc, self.maxproc - len(multiprocessing.active_children()) )
                for dummy_index in range(submit_jobs):
                    self.p[iproc].start()
                    iproc += 1
                    pend_jobs -= 1

            time.sleep(1)

        print 'Pending : 0, Running : 0, Finished : %d, [ finished ]' % njobs

    def getoutput (self):
        num = 0
        numw = 0
        missfiles = list()
        for iout in range( len(self.filelist) ):
            event, sumweight, file = self.queue.get()
            if file is not '':
                missfiles.append( file )
            else:
                num += event
                numw += sumweight
        return num, numw, missfiles


def GetPuweightFactor(PileupCfi, minBiasPileup):

    import importlib, ROOT

    m = importlib.import_module( PileupCfi )
    pileup_mc = m.mix.input.nbPileupEvents.probValue

    minBias_file = ROOT.TFile.Open( minBiasPileup, 'READ' )
    h1_minBias_pileup = minBias_file.Get('pileup')
    pileup_minBias = map( h1_minBias_pileup.GetBinContent, xrange(1, h1_minBias_pileup.GetNbinsX()+1) )
    minBias_file.Close()

    norm = sum(pileup_mc) / sum(pileup_minBias)

    pileup_reweight = list()
    for i in range( len(pileup_mc) ):
        pileup_reweight.append( pileup_minBias[i] * norm / pileup_mc[i] if pileup_mc[i] is not 0 else 0 )

    return pileup_reweight

def GetInfo(options):

    das = DASClient(options.dataset) 
    filelist = das.getFileList()
    puweight = GetPuweightFactor(options.PileupCfi ,options.minBiasPileup)
    p = ParallelCalculator(GetRealGenNumber, filelist, puweight, options.ncore)
    p.start()

    events, sumweight, missfiles = p.getoutput()
    output = { options.dataset.split('/')[1] : {
                                "Events"    : events,
                                "Weight"    : sumweight,
                                "Puweight"  : puweight,
                                "Missfile"  : missfiles
                    }
              }

    return output

def main(argv):

    options = Option_Parser(argv)

    if not os.path.isfile( options.output ):
        with open(options.output, 'w') as initf:
            initf.write( json.dumps(GetInfo(options), indent=4, sort_keys=True) )
            initf.close()
    else:
        with open(options.output, 'r+') as f:
            oldinfo = json.loads( f.read() )

            if options.dataset.split('/')[1] in oldinfo:
                if not options.force:
                    print '%s information has been exist in %s. skip !' % (options.dataset.split('/')[1], options.output)
                    f.close()
                    exit(0)
                else:
                    del oldinfo[ options.dataset.split('/')[1] ]

            oldinfo.update(GetInfo(options))
            f.seek(0)
            f.write( json.dumps(oldinfo, indent=4, sort_keys=True) )
            f.truncate()
            f.close()

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
