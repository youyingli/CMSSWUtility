#include "CMSSWUtility/Utils/interface/GlobalStyle.h"

#include "TStyle.h"

namespace plotmgr
{

    void SetGlobalStyle(){
        //Do not display any of the standard histogram decorations
        gStyle->SetOptTitle(0);
        gStyle->SetOptStat(0);
        gStyle->SetOptFit(0);
    }

}
