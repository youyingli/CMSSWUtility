import ROOT

def makeCanvas(name, xLength, yLength):
    canv = ROOT.TCanvas(name, '', xLength, yLength)
    #canv.SetTicks(1., 1.)
    canv.SetTicks()
    return canv

def makeNormalPad():
    npad = ROOT.TPad('Npad', '',0.,0.,1,0.98)
    npad.SetTopMargin(0.05)
    npad.SetBottomMargin(0.12)
    npad.SetLeftMargin(0.135)
    npad.SetRightMargin(0.06)
    return npad

def makeTopPad():
    tpad = ROOT.TPad('TPad', '', 0., 0.245, 1., 0.98)
    tpad.SetTopMargin(0.06)
    tpad.SetBottomMargin(0.019)
    tpad.SetLeftMargin(0.135)
    tpad.SetRightMargin(0.06)
    return tpad

def makeBottomPad():
    bpad = ROOT.TPad('BPad', '', 0., 0.0, 1., 0.258)
    bpad.SetTopMargin(0.0)
    bpad.SetBottomMargin(0.35)
    bpad.SetLeftMargin(0.135)
    bpad.SetRightMargin(0.06)
    return bpad

def makeLegend(xMin, yMin, xMax, yMax):
    leg = ROOT.TLegend(xMin, yMin, xMax, yMax)
    leg.SetFillStyle(0)
    leg.SetBorderSize(0)
    leg.SetTextFont(62)
    return leg


def makeRatioPlot(hNumerator, hDenominator, xTitle, yTitle, yRange = 1, color = ROOT.kBlack, style = 20, option = 'P'):

    hRatioPlot = hNumerator.Clone('hRatioPlot')
    hRatioPlot.Divide(hDenominator)
    hRatioPlot.SetTitleSize(0.15, 'xyz')
    hRatioPlot.SetLabelSize(0.15, 'xyz')
    hRatioPlot.GetYaxis().SetTitleOffset(0.4)
    hRatioPlot.GetYaxis().SetNdivisions(905)
    hRatioPlot.GetYaxis().CenterTitle(True)
    hRatioPlot.SetXTitle(xTitle)
    hRatioPlot.SetYTitle(yTitle)
    hRatioPlot.SetMinimum(1 - yRange)
    hRatioPlot.SetMaximum(1 + yRange)

    if option == 'F':
        hRatioPlot.SetFillColor(color)
        hRatioPlot.SetFillStyle(style)
    elif option == 'P':
        hRatioPlot.SetLineColor(color)
        hRatioPlot.SetMarkerColor(color)
        hRatioPlot.SetMarkerStyle(style)

    return hRatioPlot

def makeLine(plot, x, y, color, style, width, option = 'H'):

    if option == 'H':
        line = ROOT.TLine(plot.GetBinLowEdge(1), y, plot.GetBinLowEdge(plot.GetNbinsX()+1), y)
    elif option == 'V':
        line = ROOT.TLine(x, plot.GetMinimum(), x, plot.GetMaximum())

    line.SetLineColor(color)
    line.SetLineStyle(style)
    line.SetLineWidth(width)

    return line
