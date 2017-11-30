#!/usr/bin/env python

from optparse import OptionParser
import os, sys
from subprocess import Popen


def Option_Parser(argv):

    usage='usage: %prog [options] arg\n'
    usage+='This is script which can automatically produce a crab config file depending on the option you choose.\n'
    usage+='Strongly recommend check if any wrong statement is included in this config file produced\n'
    parser = OptionParser(usage=usage)

    parser.add_option('-d', '--dataset',
            type='str', dest='dataset', default='/SingleMuon/Run2017B-PromptReco-v1/MINIAOD',
            help='input your dataset like /ZMM*/*/MINIAOD from DAS'
            )
    parser.add_option('-w', '--workarea',
            type='str', dest='workarea', default=os.environ.get('USER') + '_crab',
            help='input workarea name you want. Default is your name'
            )
    parser.add_option('--Data',
            action='store_true', dest='Data',
            help='Run Real Data'
            )
    parser.add_option('--MC',
            action='store_true', dest='MC',
            help='Run MC event generation'
            )
    parser.add_option('--MCGEN',
            action='store_true', dest='MCGEN',
            help='Run MC gen'
            )
    parser.add_option('--MCSample',
            type='str', dest='MCSample', default='DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8',
            help='MC sample name you want to gen'
            )
    parser.add_option('-t', '--tag',
            type='str', dest='tag', default='RunIIFall17',
            help='tag your output dataset'
            )
    parser.add_option('-p', '--publish',
            action='store_true', dest='publish',
            help='Publish the output dataset which can find in DAS but this ouput file need EDM format'
            )
    parser.add_option('-c', '--configfile',
            type='str', dest='configfile',
            help='Input your config file like your configfile.py'
            )
    parser.add_option('--option',
            type='str', dest='option', default='',
            help='Input config file options if it needs'
            )
    parser.add_option('-o', '--outdir',
            type='str', dest='outdir', default='/store/user/youying',
            help='Output directory in some remote mechine which is specified by --remote option'
            )
    parser.add_option('--remote',
            type='str', dest='remote', default='T2_TW_NCHC',
            help='the remote mechine in which output files are stored'
            )

    (options, args) = parser.parse_args(argv)
    return options


def createCrab3Config (argv):

    options = Option_Parser(argv)

    jobname = ''
    if not options.MCGEN:
        datasetlist = options.dataset.split('/')
        jobname = datasetlist[1] + '_' + datasetlist[2]
    else:
        jobname = options.MCSample + '_GEM'

    with open(jobname + '.py', 'w') as config_file:
        config_file.write("from CRABClient.UserUtilities import config, getUsernameFromSiteDB\n")
        config_file.write("config = config()\n\n")

        config_file.write("config.section_('General')\n")
        config_file.write("config.General.requestName = '%s'\n" % jobname)
        config_file.write("config.General.workArea = '%s'\n" % options.workarea)
        config_file.write("config.General.transferOutputs = True\n")
        config_file.write("config.General.transferLogs = True\n\n")

        config_file.write("config.section_('JobType')\n")
        config_file.write("config.JobType.pluginName = '%s'\n" % ('Analysis' if not options.MCGEN else 'PrivateMC'))
        config_file.write("config.JobType.psetName = '%s'\n" % options.configfile)
        config_file.write('config.JobType.pyCfgParams = %s\n' % options.option.split())
        config_file.write("config.JobType.maxMemoryMB = 2000\n")
        config_file.write("config.JobType.maxJobRuntimeMin = 2000\n\n")

        config_file.write("config.section_('Data')\n")
        if not options.MCGEN:
            config_file.write("config.Data.inputDataset = '%s'\n" % options.dataset)
            config_file.write("config.Data.inputDBS = 'global'\n")
        else:
            config_file.write("config.Data.outputPrimaryDataset = '%s'\n" % options.MCSample)

        splittingtype = ''
        unitsPerJob = 0
        if options.Data:
            splittingtype = 'LumiBased'
            unitsPerJob = 15
        elif options.MC:
            splittingtype = 'FileBased'
            unitsPerJob = 1
        elif options.MCGEN:
            splittingtype = 'EventBased'
            unitsPerJob = 10
        config_file.write("config.Data.splitting = '%s'\n" % splittingtype)
        config_file.write("config.Data.unitsPerJob = %d\n" % unitsPerJob)
        if options.MCGEN:
            njobs = 100
            config_file.write("config.Data.totalUnits = %d\n" % (unitsPerJob * njobs))

        if options.Data:
            config_file.write("config.Data.lumiMask = 'https://cms-service-dqm.web.cern.ch/cms-service-dqm/CAF/certification/Collisions17/13TeV/PromptReco/Cert_294927-306462_13TeV_PromptReco_Collisions17_JSON.txt'\n")
        config_file.write("config.Data.outLFNDirBase = '%s'\n" % options.outdir)
        if options.publish:
            config_file.write("config.Data.publication = True\n")
        config_file.write("config.Data.outputDatasetTag = '%s'\n\n" % (options.tag + '_' + jobname))

        config_file.write("config.section_('Site')\n")
        config_file.write("config.Site.storageSite = '%s'\n" % options.remote)

    if not os.environ.get('CRAB3_PY_ROOT'):
        #os.system('source /cvmfs/cms.cern.ch/crab3/crab.sh')
        #subprocess.Popen(['source', '/cvmfs/cms.cern.ch/crab3/crab.sh'])
        Popen("source /cvmfs/cms.cern.ch/crab3/crab.sh", shell=True, executable="/bin/bash")

    print 'Writting to file %s. Do not sumbit crab jobs directly using this version! At most use crab submit --dryrun!' % jobname

if  __name__ == '__main__':
    sys.exit( createCrab3Config(sys.argv[1:]) )
