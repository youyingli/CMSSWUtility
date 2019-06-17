#!/usr/bin/env python
HTCondor="""+JobFlavour = "tomorrow"

executable  = {0}
output      = {1}
error       = {2}
log         = {3}

max_retries = 1
queue 1
"""

scriptformat="""#!/bin/bash

export X509_USER_PROXY=$HOME/.x509up_u$UID
if [ "$X509_USER_PROXY" != "" ]; then
    voms-proxy-info -all -file $X509_USER_PROXY
fi

source /cvmfs/cms.cern.ch/cmsset_default.sh

cd {0}
eval $(scram runtime -sh)
cmsRun {1} inputFiles={2} outputFile={3}
"""

from optparse import OptionParser
import os, sys
import subprocess

def Option_Parser(argv):

    usage='usage: %prog [options] arg\n'
    usage+='This is script which can automatically produce HTCondor jobs with given config file based on cmssw.\n'
    usage+='Strongly recommend check if any wrong statement is included in this config file produced\n'
    parser = OptionParser(usage=usage)

    parser.add_option('-c', '--config',
            type='str', dest='config', default='',
            help='Your config file'
            )
    parser.add_option('-u', '--UnitPerJob',
            type='int', dest='UnitPerJob', default=1,
            help='How many files will be input per job'
            )
    parser.add_option('-w', '--workspace',
            type='str', dest='workspace', default=os.environ.get('PWD') + '/',
            help='Area with program working and script storing'
            )
    parser.add_option('-i', '--intput',
            type='str', dest='input', default='',
            help='Input file with dataset file list'
            )
    parser.add_option('-d', '--dataset',
            type='str', dest='dataset', default='',
            help='Input your dataset like /ZMM*/*/MINIAOD from DAS'
            )
    parser.add_option('-o', '--outdir',
            type='str', dest='outdir', default=os.environ.get('PWD') + '/',
            help='Output file directory'
            )

    (options, args) = parser.parse_args(argv)
    return options

def getProxy():
    #if not os.path.isfile('%s/.x509up_u%d' % (os.getenv('HOME'), os.getuid())):
        #os.system('voms-proxy-init -voms cms --valid 168:00')
    os.system('grid-proxy-init -debug -verify')
    os.system('voms-proxy-init -voms cms -rfc -out ${HOME}/.x509up_u${UID} --valid 168:00')

def GetFileList(filename):

    filetype = filename.split('/')[3]

    query = 'file dataset=%s ' % filename
    if filetype == 'USER':
        query += 'instance=prod/phys03'

    print 'Opening ' + filename

    s = subprocess.Popen("dasgoclient -query='%s'" % query, shell=True, stdout=subprocess.PIPE)
    stdout, err = s.communicate()
    filelist = stdout.split('\n')

    if len(filelist) == 1:
        exit(0)
        print 'Fail to open file ! Please check %s name' % filename
    else:
        print 'Sucessfully Open ' + filename

    del filelist[-1]

    return filelist

def HTCondorSubmitter (argv):

    options = Option_Parser(argv)

    os.system('mkdir -p %s' % options.workspace)
    os.system('mkdir -p %s' % options.outdir)
    os.system('cp %s %s' % (options.config, options.workspace + '/.'))

    elefilelist = list()
    if options.dataset != '':
        elefilelist = GetFileList(options.dataset)
    elif options.input != '':
        with open(options.input, 'r') as infile:
            for elefile in infile.readlines():
                elefilelist.append(elefile)
    else:
        print 'No input dataset name or input dataset list'
        os.exit(0)

    nelefile = len(elefilelist)
    corr_num = 2 if nelefile % options.UnitPerJob != 0 else 1
    njobs = int (nelefile/options.UnitPerJob) + corr_num
    for i_job in range(1, njobs):
        start = (i_job - 1) * options.UnitPerJob
        end   =  i_job      * options.UnitPerJob if i_job * options.UnitPerJob < nelefile else nelefile

        filelist = ''
        for i in range (start, end):
            dummy = ',' if i != end - 1 else ''
            file = elefilelist[i].rstrip('\n') + dummy
            filelist += file

        runjobs = 'runjobs%d' % i_job

        with open(options.workspace + '/' + runjobs + '.sh', 'w') as config_file:
            content = scriptformat.format(
                    options.workspace,
                    options.config,
                    filelist,
                    options.outdir + '/output%d.root' % i_job
                    )
            config_file.write(content)

        os.system('chmod 755 ' + options.workspace + '/' + runjobs + '.sh')

        with open(options.workspace + '/' + runjobs + '.sub', 'w') as conder_file:
            content = HTCondor.format(
                    options.workspace + '/' + runjobs + '.sh',
                    options.workspace + '/' + runjobs + '.out',
                    options.workspace + '/' + runjobs + '.err',
                    options.workspace + '/' + runjobs + '_htc.log'
                    )
            conder_file.write(content)

        os.system('condor_submit ' + options.workspace + '/' + runjobs + '.sub')

if  __name__ == '__main__':
    getProxy()
    sys.exit( HTCondorSubmitter(sys.argv[1:]) )
