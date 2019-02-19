import ROOT

class ModifiedTH1:

    def __init__(self, th1 = None, name = None, nbin = -1, xmin = 0, xmax = 0):
        if th1:
            self._hist = th1
        elif name or nbin != -1:
            self._hist = ROOT.TH1D(name, '', nbin, xmin, xmax)
            self._hist.Sumw2()
        else:
            raise IOError("Can't find out input plot. Please input th1 plot by __init__(th1) \
                    or create new plot by __init__(th1 = None, name, nbin, xmin, xmax)")
        self._hist.SetDirectory(0)

    def close(self):
        self._hist.Delete()

    def _reset_art_style(self):
        self._hist.ResetAttLine()
        self._hist.ResetAttFill()
        self._hist.ResetAttMarker()

    def _set_common_zxis(self):
        self._hist.SetTitleFont(42,'xy')
        self._hist.SetLabelFont(42,'xy')
        self._hist.SetLabelSize(0.05,'xy')
        self._hist.SetTitleSize(0.05,'xy')
        self._hist.GetYaxis().SetTitleOffset(1.2)

    def convertToLinePlot(self, color, style):
        self._reset_art_style()
        self._hist.SetLineColor(color)
        self._hist.SetLineStyle(style)
        self._hist.SetLineWidth(3)
        self._set_common_zxis()

    def convertToFillPlot(self, color, style):
        self._reset_art_style()
        self._hist.SetLineWidth(2)
        self._hist.SetFillColor(color)
        self._hist.SetFillStyle(style)
        self._set_common_zxis()

    def convertToPointPlot (self, color, style, size):
        self._reset_art_style()
        self._hist.SetLineColor(color)
        self._hist.SetMarkerColor(color)
        self._hist.SetMarkerStyle(style)
        self._hist.SetMarkerSize(size)
        self._set_common_zxis()
        #_plot->GetYaxis()->SetTitleOffset(1.2);

    def convertToBoxErrorPlot (self, color, transparency):
        self._reset_art_style()
        self._hist.SetFillStyle(1001)
        self._hist.SetFillColorAlpha(color, 1. - transparency)
        self._hist.SetMarkerColorAlpha(color, 0.)

    def FillEntry(self, valse, weight = 1):
        self._hist.Fill(valse, weight)

    def Draw(self, drawoption):
        self._hist.Draw(drawoption)

    def setScaleWeight (self, scaleweight):
        self._hist.Scale(scaleweight)

    def normalizeToOne (self):
        factor = self._hist.Integral()

        if factor > 0.:
            self._hist.Scale(1. / factor)
        else:
            raise ValueError('%s has zero or minus entries, please check it' % self._hist.GetName())

    def setXYaxis (self, xLabel, yLabel, invisible = 'Y'):
        self._hist._plot.GetXaxis().SetTitle(xLabel)
        self._hist._plot.GetYaxis().SetTitle(yLabel)
        if invisible == 'X':
            self._hist.GetXaxis().SetLabelSize(0.)
        elif invisible == 'Y':
            self._hist.GetYaxis().SetLabelSize(0.)
        elif invisible == 'XY':
            self._hist.GetXaxis().SetLabelSize(0.)
            self._hist.GetYaxis().SetLabelSize(0.)

    def getWeightEventN (self, xmin, xmax):
        minbin = self._hist.FindBin(min)
        maxbin = self._hist.FindBin(max)
        return self._hist.Integral(minbin, maxbin);

    def setYaxisRange (self, ymin, ymax):
        self._hist.SetMinimum(ymin)
        self._hist.SetMaximum(ymax)

    def writeInFile (self):
        self._hist.Write()

    def reset (self):
        self._hist.Reset()
        self._reset_art_style()

    def addPlot (self, plot):
        self._hist.Add(plot)

    def getBinContandErr (self):
        contanderr_set = list()

        for i in range(self._hist.GetNbinsX()):
            contanderr_set.append( [self._hist.GetBinContent(i+1), self._hist.GetBinError(i+1)] )
        return contanderr_set

    def setBinContandErr (self, contanderr_set):
        if len(contanderr_set) != self._hist.GetNbinsX():
            raise IndexError("Nbin of input contents doesn't match Nbin of this plot")

        for i in range(len(contanderr_set)):
            self._hist.SetBinContent(i+1, contanderr_set[i][0])
            self._hist.SetBinError(i+1, contanderr_set[i][1])

    def getObject (self):
        return self._hist

    def getXRange (self):
        return [self._hist.GetXaxis().GetXmin(), self._hist.GetXaxis().GetXmax()]

    def getMaxContent (self):
        return self._hist.GetMaximum()

    def getNbinsX (self):
        return self._hist.GetNbinsX()

    def getBinWidth (self):
        return self._hist.GetXaxis().GetBinWidth(1)
