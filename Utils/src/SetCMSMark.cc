#include "CMSSWUtility/Utils/interface/SetCMSMark.h"

#include "TLatex.h"

namespace plotmgr
{

    void SetCMSandLUMI(double lumi, bool hasexponent)
    {
        TLatex latex;
        latex.SetNDC(true);
        latex.SetTextFont(62);
        latex.SetTextSize(0.055);
        if (hasexponent) latex.DrawLatex(0.16,0.89,"CMS");
        else latex.DrawLatex(0.135,0.96,"CMS");
        latex.SetTextFont(42);
        latex.SetTextSize(0.045);
        if (hasexponent) latex.DrawLatex(0.275,0.89,"Preliminary");
        else latex.DrawLatex(0.25,0.96,"Preliminary");
        latex.SetTextSize(0.04);
        latex.DrawLatex(0.62,0.96,Form("#sqrt{s}=13 TeV, L=%.2f fb^{-1}",lumi));
    }

}
