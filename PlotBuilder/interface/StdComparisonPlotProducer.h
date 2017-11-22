#ifndef __STDCOMPARISONPLOTPRODUCER__
#define __STDCOMPARISONPLOTPRODUCER__

#include "CMSSWUtility/Utils/interface/PlotMgrLib.h"

#include <string>
#include <vector>
#include <utility>

class StdComparisonPlotProducer{

    typedef std::vector<std::pair<double,double>> PairVector;

    public:
        StdComparisonPlotProducer(const std::string& type, const std::string& plotname, const std::string& outdir);
        ~StdComparisonPlotProducer();

        void SetBenchmark(const std::vector<std::string>& filename, bool normtounity = false);
        void SetReference(const std::vector<std::string>& filename, const std::string& tagname,  Color_t color, Style_t style, double shift_factor = 1., bool showfactor = false);
        void SetComparison(const std::vector<std::string>& filenames, const std::string& tagname, Color_t color ,Style_t style, double scale_factor = 1., bool showfactor = false, bool normtounity = false);
        void SetLogScale(bool islog = true);
        void SetLumi(double lumi = 10.);
        void SetSystError(const PairVector& systerror, bool dosysts);
        void DrawDriven(const std::string& xtitle, const std::string& unit);


    private:
        plotmgr::TH1Service<TH1F> _th1service;

        bool _issignal;
        bool _isbkg;
        bool _isdata;
        bool _islog;
        bool _dosysts;
        int _nbin;
        double _lumi;
        std::string _type;
        std::string _plotname;
        std::string _outdir;
        TCanvas* _canv;
        THStack* _stackplot;
        TLegend* _legend;
        std::vector<ModifiedTH1<TH1F>*> _signalcollection;
        std::vector<TH1F*> _backgroundcollection;
        PairVector _systerror;
        PairVector _totalcontent;
        PairVector _totalrcontent;
        //private function
        void PackPlot (const std::vector<std::string>& filenames, const string& tagname);
        void GetTotalMCError(bool addsysts);
        void end();

};


#endif 
