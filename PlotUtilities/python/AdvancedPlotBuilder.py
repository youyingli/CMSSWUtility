from CMSSWUtility.Utils.TH1Service import TH1Service
from CMSSWUtility.Utils.PlotObject import *
from CMSSWUtility.Utils.GlobalPlotSetting import *
from CMSSWUtility.Utils.CMSMark import *
import ROOT
import os
import math

class AdvancedPlotBuilder:

    def __init__(self, plotname, lumi, outdir):

        self._plotname = plotname
        self._lumi = lumi
        self._outdir = outdir
        self._th1service = TH1Service()
        self._stackplot = ROOT.THStack('hs', '')
        self._legend = makeLegend(0.5, 0.7, 0.92, 0.92)
        self._legend.SetNColumns(2)
        self._bkgcollection = list()
        self._sigcollection = list()
        self._bkginfos = list()
        self._systlist = list()

    # Data mc
    def setBenchMark(self, filenames, color, style, legname, normtounity = False):
        self._makePackedPlots('hData', filenames)
        if normtounity:
            self._th1service.getPlot('hData').normalizeToOne()
        self._th1service.getPlot('hData').convertToPointPlot(color, style, 0.8)
        self._legend.AddEntry(self._th1service.getPlot('hData').getObject(), legname, 'PL')

    # signal mc
    def setReference(self, tagname, filenames, color, style, legname, shift_factor = 1.):
        self._makePackedPlots(tagname, filenames)
        self._th1service.getPlot(tagname).setScaleWeight(shift_factor * self._lumi)
        self._th1service.getPlot(tagname).convertToLinePlot(color, style)

        legstr = tagname + ' x ' + str(shift_factor) if shift_factor != 1. else tagname
        self._legend.AddEntry(self._th1service.getPlot(tagname).getObject(), legstr, 'L')
        self._sigcollection.append(tagname)

    # bkg mc
    def setComparison(self, tagname, filenames, color, style, legname, scale_factor = 1., normtounity = False):
        self._makePackedPlots(tagname, filenames)
        if normtounity:
            self._th1service.getPlot(tagname).normalizeToOne()
        else:
            self._th1service.getPlot(tagname).setScaleWeight(scale_factor * self._lumi)

        self._th1service.getPlot(tagname).convertToFillPlot(color, style)
        self._stackplot.Add(self._th1service.getPlot(tagname).getObject())

        self._legend.AddEntry(self._th1service.getPlot(tagname).getObject(), legname, 'F')
        self._bkgcollection.append(tagname)
        for filename in filenames:
            self._bkginfos.append([filename.replace('.root', ''), scale_factor * self._lumi])

    def includeSystematics(self, systlist):
        self._systlist = systlist

#    def drawDrivenOne(xTitle, unit):

    def drawDrivenTwo(self, xTitle, unit, isLog = False):
        xrange = self._th1service.getPlot('hData').getXRange()
        self._nbin = self._th1service.getPlot('hData').getNbinsX()
        self._th1service.addNewTH1('hBkg', self._nbin, xrange[0], xrange[1])

        globalPlotSetting()

        for bkg in self._bkgcollection:
            self._th1service.getPlot('hBkg').addPlot(self._th1service.getPlot(bkg).getObject())

        # ------------------------------------------------------------
        up_down_error2 = self._doSystErrorPropagator(self._systlist)
        totalerror = self._setTotalError(up_down_error2)
        self._th1service.addNewTH1('ErrorPlot',  self._nbin, xrange[0], xrange[1])
        self._th1service.addNewTH1('ErrorPlotr', self._nbin, xrange[0], xrange[1])
        self._th1service.getPlot('ErrorPlot').setBinContandErr(totalerror[0])
        self._th1service.getPlot('ErrorPlotr').setBinContandErr(totalerror[1])
        self._th1service.getPlot('ErrorPlot').convertToBoxErrorPlot(ROOT.kGray+2, 0.55)
        self._th1service.getPlot('ErrorPlotr').convertToBoxErrorPlot(ROOT.kGray+2, 0.55)

        errleg = 'Stat. #oplus Syst.' if len(self._systlist) != 0 else  'Stat. Uncert.'
        self._legend.AddEntry(self._th1service.getPlot('ErrorPlot').getObject(), errleg, 'F')

        canvas = makeCanvas(self._plotname + '_canv', 600, 700)
        canvas.cd()

        tpad = makeTopPad()
        tpad.Draw()
        tpad.cd()

        self._stackplot.Draw('histo')
        self._stackplot.GetXaxis().SetLabelSize(0.)
        self._stackplot.GetYaxis().SetTitle('Events/(%.2f %s)' % (self._stackplot.GetXaxis().GetBinWidth(1), unit))
        self._stackplot.GetYaxis().SetTitleOffset(1.3)
        self._stackplot.GetHistogram().SetTitleFont(42,'xyz')
        self._stackplot.GetHistogram().SetLabelFont(42,'xyz')
        self._stackplot.GetHistogram().SetTitleSize(0.05,'xyz')
        self._stackplot.GetHistogram().SetLabelSize(0.05,'xyz')

        self._th1service.getPlot('ErrorPlot').Draw('E2 same')
        self._th1service.getPlot('hData').Draw('E1 X0 same')

        for sig in self._sigcollection:
            self._th1service.getPlot(sig).Draw('histosame')
        self._th1service.getPlot('hData').Draw('E1 X0 same')

        if isLog:
            tpad.SetLogy()
            self._stackplot.SetMinimum(0.01)
            self._stackplot.SetMaximum(800 * self._th1service.getPlot('hData').getMaxContent())
        else:
            ROOT.TGaxis.SetMaxDigits(4)
            self._stackplot.SetMinimum(0.)
            self._stackplot.SetMaximum(1.6 * self._th1service.getPlot('hData').getMaxContent())

        self._legend.Draw()
        plotContent = makeCMSMark(self._lumi)

        canvas.Update()

        canvas.cd()

        bpad = makeBottomPad()
        bpad.Draw()
        bpad.cd()

        ratioPlot = makeRatioPlot(self._th1service.getPlot('hData').getObject(), \
                                  self._th1service.getPlot('hBkg') .getObject(), \
                                  xTitle + '(' + unit + ')', 'Data/MC')
        ratioPlot.Draw('E1 X0')
        self._th1service.getPlot('ErrorPlotr').Draw('E2 same')
        hline = makeLine(ratioPlot, 0, 1, ROOT.kBlue, 7, 3)
        hline.Draw()
        ratioPlot.Draw('E1 X0 same')

        canvas.Update()

        os.system('mkdir -p ' + self._outdir)
        canvas.Print('%s/%s.pdf' % (self._outdir, self._plotname))
        canvas.Close()

    def _makePackedPlots(self, tagname, filenames):

        isfirst = True
        i = 1
        for fi in filenames:
            if isfirst:
                self._th1service.addPlotFromFile(tagname, self._plotname, fi)
                isfirst = False
            else:
                self._th1service.addPlotFromFile(tagname + str(i), self._plotname, fi)
                self._th1service.getPlot(tagname).addPlot(self._th1service.getPlot(tagname + str(i)).getObject())
            i += 1

    def _setTotalError(self, systerror2):

        total = list()
        totalr= list()

        bkg = self._th1service.getPlot('hBkg').getBinContandErr()

        for i in range(self._nbin):

            if bkg[i][0] == 0.:
                total.append([0., 0.])
                totalr.append([0., 0.])
            elif len(self._systlist) != 0:
                totalup   = math.sqrt(bkg[i][1] * bkg[i][1] + systerror2[0][i])
                totaldown = math.sqrt(bkg[i][1] * bkg[i][1] + systerror2[1][i])
                up   = bkg[i][0] + totalup
                down = bkg[i][0] - totaldown
                total. append ([(up + down) * 0.5, (up - down) * 0.5])
                totalr.append ([(up + down) * 0.5 / bkg[i][0], (up - down) * 0.5 / bkg[i][0]])
            else:
                total.append( [bkg[i][0], bkg[i][1]] )
                totalr.append( [1., bkg[i][1] / bkg[i][0]] )

        return total, totalr


    def _doSystErrorPropagator(self, systlabels):
        systplotservice = TH1Service()
        systplotservice.addPlotFromFile('hdummy', self._plotname, self._bkginfos[0][0] + '.root')
        nbin = systplotservice.getPlot('hdummy').getNbinsX()
        uperror2   = [0.] * nbin
        downerror2 = [0.] * nbin

        for systlabel in systlabels:
            for bkginfo in self._bkginfos:
                systplotservice.addPlotFromFile('hnormal', self._plotname, bkginfo[0] + '.root')
                systplotservice.addPlotFromFile('hup',     self._plotname, bkginfo[0] + '_' + systlabel + 'Up01sigma.root')
                systplotservice.addPlotFromFile('hdown',   self._plotname, bkginfo[0] + '_' + systlabel + 'Down01sigma.root')
                systplotservice.getPlot('hnormal').setScaleWeight(bkginfo[1])
                systplotservice.getPlot('hup')    .setScaleWeight(bkginfo[1])
                systplotservice.getPlot('hdown')  .setScaleWeight(bkginfo[1])

                normal = systplotservice.getPlot('hnormal').getBinContandErr()
                up     = systplotservice.getPlot('hup')    .getBinContandErr()
                down   = systplotservice.getPlot('hdown')  .getBinContandErr()

                for i in range(nbin):
                    if up[i][0] - normal[i][0] >= 0.:
                        uperror2[i] += math.pow(up[i][0] - normal[i][0], 2.0)
                    if normal[i][0] - down[i][0] >= 0.:
                        downerror2[i] += math.pow(normal[i][0] - down[i][0], 2.0)

                systplotservice.delete('hnormal')
                systplotservice.delete('hup')
                systplotservice.delete('hdown')

        systplotservice.close()

        return uperror2, downerror2
