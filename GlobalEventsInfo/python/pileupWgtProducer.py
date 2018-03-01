import FWCore.ParameterSet.Config as cms
from optparse import OptionParser
import ROOT
import sys
from array import array

def Option_Parser(argv):

    usage='usage: %prog [options] arg\n'
    usage+='The script will output pileup weight from given pileup cfi and pileup of min bias events.\n'
    parser = OptionParser(usage=usage)

    parser.add_option('--PileupCfi',
            type='str', dest='PileupCfi', default='mix_2016_25ns_SpringMC_PUScenarioV1_PoissonOOTPU_cfi',
            help='Input pile up cfi file. It can be found in SimGeneral/MixingModule/python/'
            )
    parser.add_option('--minbiasPileup',
            type='str', dest='minBiasPileup', default='MyDataPileupHistogram.root',
            help='tag output MC samples'
            )
    parser.add_option('-o', '--output',
            type='str', dest='output', default='/afs/cern.ch/user/<Y>/<YOURNAME>',
            help='Output directory'
            )

    (options, args) = parser.parse_args(argv)
    return options

def make_pileupweight(argv):

    options = Option_Parser(argv)
    process = cms.Process('pileup')

    pileup_cfi = 'SimGeneral.MixingModule.' + options.PileupCfi
    print 'Load %s' % pileup_cfi
    process.load(pileup_cfi)

    pileupbins  = array('d', process.mix.input.nbPileupEvents.probFunctionVariable)
    pileupvalue = array('d', process.mix.input.nbPileupEvents.probValue)
    pileupbins += array('d', [pileupbins[-1] + pileupbins[1] - pileupbins[0]] )

    h1_mc_pileup_mix = ROOT.TH1D('h1_mc_pileup_mix', '', len(pileupbins)-1, array('d',pileupbins))

    for x,y in zip(xrange(len(pileupvalue)), pileupvalue):
        h1_mc_pileup_mix.SetBinContent(x+1,y)

    minBias_file = ROOT.TFile(options.minBiasPileup)
    h1_minBias_pileup_tmp = minBias_file.Get('pileup')
    h1_minBias_pileup = h1_minBias_pileup_tmp.Clone('h1_minBias_pileup')
    h1_minBias_pileup.Scale(1. / h1_minBias_pileup_tmp.Integral())

    h1_pileup_ratio = h1_minBias_pileup.Clone('h1_pileup_ratio')
    h1_pileup_ratio.Divide(h1_mc_pileup_mix)
    h1_pileup_ratio.SetOption('hist')

    outfile = ROOT.TFile(options.output, 'recreate')
    h1_mc_pileup_mix.Write()
    h1_minBias_pileup.Write()
    h1_pileup_ratio.Write()
    outfile.Close()

if __name__ == '__main__':
    sys.exit(make_pileupweight(sys.argv[1:]))

