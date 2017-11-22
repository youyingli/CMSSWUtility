#include "CMSSWUtility/PlotBuilder/interface/StdComparisonPlotProducer.h"
#include "CMSSWUtility/PlotBuilder/interface/LatexDraw.h"

#include "TFile.h"
#include "TGaxis.h"

#include <iostream>
#include <cassert>

using namespace std;

StdComparisonPlotProducer::StdComparisonPlotProducer(const string& type, const string& plotname, const string& outdir):
    _type(type),
    _plotname(plotname),
    _outdir(outdir)
{
    system(Form("mkdir -p %s", _outdir.c_str()));
    _stackplot = new THStack("hs", "");
    _legend = plotmgr::NewLegend();
    _legend->SetNColumns(2);
    _issignal = false;
    _isbkg    = false;
    _isdata   = false;
    _islog    = false;
    _dosysts  = false;
}

StdComparisonPlotProducer::~StdComparisonPlotProducer()
{
    delete _stackplot;
    _stackplot = NULL;
    _th1service.Close();
}

void StdComparisonPlotProducer::SetBenchmark (const vector<string>& filenames, bool normtounity)
{
    PackPlot(filenames, "hData");
    if (normtounity) _th1service.GetPlot("hData")->SetScaleWeight(1. / _th1service.GetPlot("hData")->GetEventN());
    _th1service.GetPlot("hData")->ConvertToPointPlot(kBlack, 20, 0.8);
    _legend->AddEntry(_th1service.GetPlot("hData")->GetSnapShot(), "hData", "PL");
    _isdata = true;
}

void StdComparisonPlotProducer::SetReference (const vector<string>& filenames, const string& tagname, Color_t color, Style_t style, double shift_factor, bool showfactor)
{
    PackPlot(filenames, tagname);
    _th1service.GetPlot(tagname)->SetScaleWeight(shift_factor);
    _th1service.GetPlot(tagname)->ConvertToLinePlot(color, style);
    string legstr = showfactor ? (tagname + " x " + to_string(shift_factor)) : tagname;
    _legend->AddEntry(_th1service.GetPlot(tagname)->GetSnapShot(), legstr.c_str(), "L");
    _signalcollection.emplace_back(_th1service.GetPlot(tagname));
    _issignal = true;

    cout << tagname << " (expected) : " << _th1service.GetPlot(tagname)->GetEventN() / shift_factor << endl;
}

void StdComparisonPlotProducer::SetComparison (const vector<string>& filenames, const string& tagname, Color_t color ,Style_t style, double scale_factor, bool showfactor, bool normtounity)
{
    PackPlot(filenames, tagname);
    _th1service.GetPlot(tagname)->SetScaleWeight(scale_factor);
    if (normtounity) _th1service.GetPlot(tagname)->SetScaleWeight(1./_th1service.GetPlot(tagname)->GetEventN());
    _backgroundcollection.emplace_back(_th1service.GetPlot(tagname)->GetSnapShot());
    _th1service.GetPlot(tagname)->ConvertToFillPlot(color, style);
    _stackplot->Add(_th1service.GetPlot(tagname)->GetSnapShot());
    string legstr = showfactor ? (tagname + " x " + to_string(scale_factor)) : tagname;
    _legend->AddEntry(_th1service.GetPlot(tagname)->GetSnapShot(), legstr.c_str(), "F");
    _isbkg = true;
}

void StdComparisonPlotProducer::SetLogScale (bool islog)
{
    cout << "dklk." << endl;
    _islog = islog;
}

void StdComparisonPlotProducer::DrawDriven (const string& xtitle, const string& unit)
{
    assert(_isbkg && _isdata);

    auto xrange = _th1service.GetPlot("hData")->GetXRange();
    _nbin = _th1service.GetPlot("hData")->GetNbinsX();
    _th1service.AddNewTH1("hBkg", _nbin, xrange.first, xrange.second);
    for (const auto& it : _backgroundcollection) {
        _th1service.GetPlot("hBkg")->AddPlot(it); 
    }

    plotmgr::SetGlobalStyle();

    // Add MC Uncertainties (Stat , Syst)    
    //------------------------------------------------------------------------------------------------------------------
    GetTotalMCError(_dosysts);
    _th1service.AddNewTH1("ErrorPlot", _nbin, xrange.first, xrange.second);
    _th1service.AddNewTH1("ErrorPlotr", _nbin, xrange.first, xrange.second);
    _th1service.GetPlot("ErrorPlot")->SetBinContent(_totalcontent);
    _th1service.GetPlot("ErrorPlot")->ConvertToBoxErrorPlot(kGray+2, 0.55);
    _th1service.GetPlot("ErrorPlotr")->SetBinContent(_totalrcontent);
    _th1service.GetPlot("ErrorPlotr")->ConvertToBoxErrorPlot(kGray+2, 0.55);
    string legstr = _dosysts ? "Stat. #oplus Syst." : "Stat. Uncert.";
    _legend->AddEntry(_th1service.GetPlot("ErrorPlot")->GetSnapShot(), legstr.c_str(), "F");
    //------------------------------------------------------------------------------------------------------------------

    //Cancas
    _canv = plotmgr::NewCanvas(); _canv->cd();

    //Top Pad
    //------------------------------------------------------------------------------------------------------------------
    TPad* toppad = plotmgr::NewTopPad(); toppad->Draw(); toppad->cd();
    _stackplot->Draw("histo");
    _th1service.GetPlot("ErrorPlot")->Draw("E2 same");
    if (_issignal) 
        for (const auto& it : _signalcollection) it->Draw("histosame");
    _th1service.GetPlot("hData")->Draw("E1 X0 same");

    _stackplot->GetXaxis()->SetLabelSize(0.);
    _stackplot->GetYaxis()->SetTitle(Form("Events/(%.2f %s)", _stackplot->GetXaxis()->GetBinWidth(1), unit.c_str()));
    _stackplot->GetYaxis()->SetTitleOffset(1.3);
    _stackplot->GetHistogram()->SetTitleFont(42,"xyz");
    _stackplot->GetHistogram()->SetLabelFont(42,"xyz");
    _stackplot->GetHistogram()->SetLabelSize(0.04,"xyz");
    _stackplot->GetHistogram()->SetTitleSize(0.04,"xyz");

    if (_islog) {
        toppad->SetLogy();
        _stackplot->SetMinimum(0.01);
        _stackplot->SetMaximum(800 * _th1service.GetPlot("hData")->GetMaxContent());
        AddLatexContent(_lumi, _type);
    } else {
        TGaxis::SetMaxDigits(4);
        _stackplot->SetMinimum(0.);
        _stackplot->SetMaximum(1.6 * _th1service.GetPlot("hData")->GetMaxContent());
        AddLatexContent(_lumi, _type, _stackplot->GetMaximum() >= 10000.);
    }
    
    _legend->Draw();
    //------------------------------------------------------------------------------------------------------------------

    _canv->Update();

    //Bottom Plot
    //------------------------------------------------------------------------------------------------------------------
    _canv->cd();
    TPad* bottomPad = plotmgr::NewBottomPad(); bottomPad->Draw(); bottomPad->cd();
    TH1* comparePlot = plotmgr::RatioPlot(_th1service.GetPlot("hData")->GetSnapShot(), 
                                          _th1service.GetPlot("hBkg")->GetSnapShot(), 
                                          Form("%s",xtitle.c_str()), "Data/MC");
    comparePlot->Draw("E1 X0");
    _th1service.GetPlot("ErrorPlotr")->Draw("E2 same");
    TLine* horizonline = plotmgr::NewHorizontalLine(comparePlot, 1, kBlue, 7, 3);
    horizonline->Draw();
    comparePlot->Draw("E1 X0 same");
    //------------------------------------------------------------------------------------------------------------------

    _canv->Update();
    end();
}


void StdComparisonPlotProducer::end ()
{
    system(Form("mkdir -p %s",_outdir.c_str()));
    _canv->Print(Form("%s/%s.pdf",_outdir.c_str(),_plotname.c_str()));
    _canv->Close();
}

void StdComparisonPlotProducer::SetLumi (double Lumi)
{
    _lumi = Lumi;
}

void StdComparisonPlotProducer::SetSystError (const PairVector& systerror, bool dosysts)
{
    _systerror = systerror;
    _dosysts = dosysts;
}

void StdComparisonPlotProducer::PackPlot (const vector<string>& filenames, const string& tagname)
{
    bool ismulti = false;
    int count = 0;
    for (const auto& it : filenames) {
        if (ismulti) {
            _th1service.AddPlotFromFile(tagname + to_string(count), _plotname, it);
            _th1service.GetPlot(tagname)->AddPlot(_th1service.GetPlot(tagname + to_string(count))->GetSnapShot());
        } else {
            _th1service.AddPlotFromFile(tagname, _plotname, it);
            ismulti = true;
        }
        count++;
    }
}

void StdComparisonPlotProducer::GetTotalMCError (bool addsysts)
{
    auto bkgcontent = _th1service.GetPlot("hBkg")->GetBinContent();

    for (int i = 0; i < _nbin; i++) {
        if (bkgcontent[i].first == 0.) {
            _totalcontent.emplace_back(make_pair(0.,0.));
            _totalrcontent.emplace_back(make_pair(0.,0.));
        } else if (addsysts) {
            double totalup = sqrt(pow(bkgcontent[i].second, 2.0) + pow(_systerror[i].first, 2.0));
            double totaldown = sqrt(pow(bkgcontent[i].second, 2.0) + pow(_systerror[i].second, 2.0));
            double upvalue = totalup + bkgcontent[i].first;
            double downvalue =  bkgcontent[i].first - totaldown;
            _totalcontent .emplace_back(make_pair((upvalue + downvalue) / 2., (upvalue - downvalue) / 2.));
            _totalrcontent.emplace_back(make_pair((upvalue + downvalue) / (2. * bkgcontent[i].first), (upvalue - downvalue) / (2. * bkgcontent[i].first)));
        } else {
            _totalcontent .emplace_back(make_pair(bkgcontent[i].first, bkgcontent[i].second));
            _totalrcontent.emplace_back(make_pair(1., bkgcontent[i].second / bkgcontent[i].first));
        }
    }//i++
}

