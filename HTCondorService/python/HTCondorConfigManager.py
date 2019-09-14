#!/usr/bin/env python
JobConfig="""{0}
    "Tag"         :  "the tag for this job",
    "Executable"  :  "myConfit.py or executable file",
    "Dataset"     :  "/DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8/RunIIFall17DRPremix-PU2017_94X_mc2017_realistic_v11_ext1-v1/AODSIM or txt with file directories",
    "LumiMask"    :  "Goldjson file for example",
    "CmdLine"     :  "Your Executable option",
    "UnitPerJob"  :  "Number of input root file per job",
    "QUEUE"       :  "Which queue do you want? Choose one of the following options:
                    espresso     = 20 minutes
                    microcentury = 1 hour
                    longlunch    = 2 hours
                    workday      = 8 hours
                    tomorrow     = 1 day
                    testmatch    = 3 days
                    nextweek     = 1 week   "
    "NCPU"        :  "Number of cpu",
    "Workspace"   :  "program run area. Must be under CMSSW",
    "Outdir"      :  "output file directory",
    "EDM"         :  "True for edm framework",
    "DataType"    :  "data, MC or other"
{1}
"""

Default = { 'Tag'        : '',           
            'LumiMask'   : '',           
            'CmdLine'    : '',           
            'UnitPerJob' : '1',          
            'QUEUE'      : 'tomorrow',   
            'NCPU'       : '1',          
            'EDM'        : 'True'        
          }

MustBeKeyValue = ["Executable", "Dataset", "Workspace", "Outdir", "DataType"]

import os, sys
import json

class HTCondorConfigManager:

    def ConfigProducer(self):
        with open('htcondor_cfg.json', 'w') as htcondor_cfg:
            content = JobConfig.format(
                    '{',
                    '}'
                    )
            htcondor_cfg.write(content)

    def Load(self, htcondor_cfg):

        print 'Loading the HTCondor config file %s ...' % htcondor_cfg

        with open(htcondor_cfg, 'r') as file:
            htcondor_dict = json.loads(file.read())
            self._default_assign(htcondor_dict)
            self._config_check(htcondor_dict)

        for key, value in htcondor_dict.items():
            setattr(self, key, value)

        print 'Successfully load the config file %s !' % htcondor_cfg

    def _default_assign(self, config_dict):
        for key, value in Default.items():
            if not config_dict.has_key(key):
                config_dict[key] = value

    def _config_check(self, config_dict):

        for key in MustBeKeyValue:
            if not config_dict.has_key(key):
                print 'You are missing %s in your input config file.' % key
                sys.exit(0)

            if config_dict[key] == '':
                print "Your %s is empty" % key
                sys.exit(0)
