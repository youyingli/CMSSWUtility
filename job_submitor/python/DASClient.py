#!/usr/bin/env python
import os, sys
import subprocess
import json

class DASClient:

    def __init__(self, filename):

        self.filename = filename
        self.query = 'dataset=%s ' % filename
        filetype = filename.split('/')[3]

        if filetype == 'USER':
            self.query += 'instance=prod/phys03'
        if filetype == 'AODSIM' or filetype == 'MINIAODSIM':
            self.isMC = True

    def _dasclient(self, prefix, postfix):

        self.query = prefix + self.query

        s = subprocess.Popen("dasgoclient -query='%s' %s" % (self.query, postfix), shell=True, stdout=subprocess.PIPE)
        stdout, err = s.communicate()
        if err != None:
            print err
            sys.exit()
        output = stdout.split('\n')

        return output


    def getFileList(self):

        output = self._dasclient( 'file ', '' )

        del output[-1]
        return output

    def getLumiSection(self):

        if self.isMC:
            print 'MC can not have real limu section'
            sys.exit()

        output = self._dasclient( 'run,lumi ', '-json' )

        lumi_section = {}

        for i_output in output[1:-2]:
            index = 0

            if i_output[len(i_output)-1] == ',':
                index = -2
            else:
                index = len(i_output)
            output_dict = json.loads(i_output[0:index])

            run_number = output_dict['run'][0]['run_number']
            lumi_list  = output_dict['lumi'][0]['number']
            lumi_list.sort()

            tmp_lumi_section = [ lumi_list[0], lumi_list[-1] ]
            packed_lumi_section = [ tmp_lumi_section ]
            lumi_section.setdefault( run_number, packed_lumi_section )

        lumifile = self.filename.split('/')[1] + self.filename.split('/')[2] + '_lumisection.json'
        with open(lumifile, 'w') as outfile:
            json.dump(lumi_section, outfile, indent=4, sort_keys=True)
