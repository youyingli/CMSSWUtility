import ROOT

def makeCMSMark(lumi):

    latex = ROOT.TLatex()
    latex.SetNDC(True)
    latex.SetTextFont(62)
    latex.SetTextSize(0.06)
    latex.DrawLatex(0.17,0.86,'CMS')
    latex.SetTextFont(42)
    latex.SetTextSize(0.05)
    latex.DrawLatex(0.29,0.865,'Preliminary')
    latex.SetTextSize(0.055)
    latex.DrawLatex(0.62,0.94, '%.1f fb^{-1} (13TeV)' % lumi)

    return latex


#    latex.DrawLatex(0.16, 0.89, '#font[62]{CMS}')
