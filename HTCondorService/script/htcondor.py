#!/usr/bin/env python
HTCondor_control="""+JobFlavour = "{0}"

executable  = {1}/runjobs.sh
arguments   = $(infile) $(outfile)

output      = {1}/output/hello.$(ClusterId).$(ProcId).out
error       = {1}/error/hello.$(ClusterId).$(ProcId).err
log         = {1}/log/hello.$(ClusterId).log

max_retries = 1
queue infile,outfile from {1}/IORecord.dat
"""

scriptformat="""#!/bin/bash

export X509_USER_PROXY={0}/.x509up_u{1}
if [ "$X509_USER_PROXY" != "" ]; then
    voms-proxy-info -all -file $X509_USER_PROXY
fi

source /cvmfs/cms.cern.ch/cmsset_default.sh

cd {2}
eval $(scram runtime -sh)
cmsRun {3} {4} inputFiles=$(cat $1) outputFile=$2
"""

from optparse import OptionParser
from CMSSWUtility.job_submitor.DASClient import DASClient
from CMSSWUtility.HTCondorService.HTCondorConfigManager import HTCondorConfigManager
import os, sys
import json
import subprocess

def Option_Parser(argv):

    usage='usage: %prog [options] arg\n'
    usage+='This is script which can automatically produce HTCondor jobs with given config file based on cmssw.\n'
    usage+='Strongly recommend check if any wrong statement is included in this config file produced\n'
    parser = OptionParser(usage=usage)

    parser.add_option('-c', '--config',
            type='str', dest='config', default='',
            help='Input your config file'
            )
    parser.add_option('-q', '--queue',
            type='str', dest='queue', default='tomorrow',
            help='Time limit for jobs. For example, espresso     = 20 minutes, microcentury = 1 hour, longlunch    = 2 hours    \
            workday      = 8 hours, tomorrow     = 1 day, testmatch    = 3 days, nextweek     = 1 week'
            )
    parser.add_option( '--submit',
            action='store_true', dest='submit',
            help='Submit HTCondor job to cluster'
            )
    parser.add_option( '-d', '--dir',
            type='str', dest='dir', default='',
            help='Directory where the jobs are'
            )
    parser.add_option( '--resubmit',
            action='store_true', dest='resubmit',
            help='Resubmit the jobs after using --debug'
            )
    parser.add_option( '--debug',
            action='store_true', dest='debug',
            help='Print the error and produce the resubmit file in the given job directory by'
            )
    parser.add_option( '--dryrun',
            action='store_true', dest='dryrun',
            help='Create job directory but do not submit'
            )
    parser.add_option( '--template',
            action='store_true', dest='template',
            help='Produce a JobConfig file for submission'
            )

    (options, args) = parser.parse_args(argv)
    return options

class HTCondorJobManager:

    def __init__(self, job_config):

        self.job_config = job_config
        if not os.path.exists(self.job_config.Executable):
            print 'Your Executable does not exist in given area like %s' % self.job_config.Executable

    def JobSplitter (self):

        jobname = ''
        filelist = list()

        if self.job_config.Dataset != '':
            das = DASClient(self.job_config.Dataset)
            filelist = das.getFileList()

            dataset_list = self.job_config.Dataset.split('/')
            jobname = dataset_list[1] + '_' + dataset_list[2]
        #elif options.input != '':
        #    with open(options.input, 'r') as infile:
        #        for elefile in infile.readlines():
        #            elefilelist.append(elefile)
        else:
            print 'No input dataset name or input dataset list'
            sys.exit(0)

        self.job_dir = self.job_config.Workspace + '/' + self.job_config.Tag + '/' + jobname
        self.out_dir = self.job_config.Outdir    + '/' + self.job_config.Tag + '/' + jobname + '/output'
        os.system('mkdir -p %s' % self.job_dir)
        os.system('mkdir -p %s' % self.out_dir)

        nfile = len(filelist)
        unit = int(self.job_config.UnitPerJob)

        corr_num = 1 if nfile % unit!= 0 else 0
        njobs = nfile/unit + corr_num

        IORecord = []
        for i_job in range(0, njobs):
            start =  i_job      * unit
            end   = (i_job + 1) * unit if (i_job + 1) * unit < nfile else nfile
            file_t = ",".join(map(lambda x: "%s" % x, filelist[start:end]))

            inputfile = self.job_dir + '/inputfile%d.txt' % i_job
            with open(inputfile, "w") as file:
                file.write(file_t)
            IORecord.append( inputfile + ", %s/output%d.root" % (self.out_dir, i_job ) )

        with open(self.job_dir + "/IORecord.dat", "w") as file:
            for ior in IORecord:
                file.write(ior + "\n")

    def ExecutableManager(self, dryrun):

        exelist = self.job_config.Executable.split()
        self.exe = self.job_dir + '/' + exelist[-1]

        os.system('cp %s %s' % (self.job_config.Executable , self.exe))

        if self.job_config.EDM == 'False':
            pass
        else:
            with open(self.exe, 'a+') as exefile:
                content = exefile.read()
                exefile.write("\n#HTCondor IO configuration set\n\n")

                if content.find('VarParsing') == -1:
                    exefile.write("from FWCore.ParameterSet.VarParsing import VarParsing\n")
                    exefile.write("options = VarParsing ('analysis')\n")
                    exefile.write("options.parseArguments()\n\n")

                if self.job_config.DataType == 'Data':
                    exefile.write("import FWCore.PythonUtilities.LumiList as LumiList\n")
                    exefile.write("ss.source.lumisToProcess = LumiList.LumiList( filename = '%s' ).getVLuminosityBlockRange()\n\n" % self.job_config.LumiMask)

                exefile.write("process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(%d) )\n" % 300 if dryrun else -1)
                exefile.write("process.source = cms.Source ('PoolSource', fileNames = cms.untracked.vstring( options.inputFiles ))\n")
                exefile.write("process.TFileService = cms.Service('TFileService', fileName = cms.string( options.outputFile ))\n\n")

    def JobMaterialProducer (self, queue):

        os.system('mkdir -p %s/output' % self.job_dir)
        os.system('mkdir -p %s/error' % self.job_dir)
        os.system('mkdir -p %s/log' % self.job_dir)

        with open(self.job_dir + '/runjobs.sh', 'w') as script:
            content = scriptformat.format(
                    os.getenv('HOME'),
                    os.geteuid(),
                    self.job_dir,
                    self.exe,
                    self.job_config.CmdLine
                    )
            script.write(content)

        os.system('chmod 755 ' + self.job_dir + '/runjobs.sh')

        with open(self.job_dir + '/runjobs.sub', 'w') as conder_file:
            content = HTCondor_control.format(
                    queue,
                    self.job_dir
                    )
            conder_file.write(content)

    def JobSubmitter(self):
        os.system('condor_submit %s/runjobs.sh' % self.job_dir)

def getProxy():
    if not os.path.exists('%s/.x509up_u%d' % (os.getenv('HOME'), os.getuid())):
        os.system('grid-proxy-init -debug -verify')
        os.system('voms-proxy-init -voms cms -rfc -out ${HOME}/.x509up_u${UID} --valid 168:00')


def HTCondor (argv):

    options = Option_Parser(argv)

    jobConfig = HTCondorConfigManager()

    if options.template:
        jobConfig.ConfigProducer()
        sys.exit()

    if options.submit:

        if options.config == '':
            print 'Please input your HTCondor config file'
            sys.exit()
        else:
            jobConfig.Load(options.config)

        htc_mgr = HTCondorJobManager(jobConfig)
        htc_mgr.JobSplitter()
        htc_mgr.ExecutableManager(options.dryrun)
        htc_mgr.JobMaterialProducer(options.queue)

        if not options.dryrun:
            htc_mgr.JobSubmitter()
            print 'Your jobs have been submitted in HTCondor cluster !'

if  __name__ == '__main__':
    getProxy()
    sys.exit( HTCondor(sys.argv[1:]) )
