#ifndef __TH1SERVICE_HPP__
#define __TH1SERVICE_HPP__

#include "CMSSWUtility/Utils/interface/ModifiedTH1.hpp"

#include "TFile.h"

#include <string>
#include <map>

namespace plotmgr
{

    template <typename TH1Type>
    class TH1Service {
    
        public:
            TH1Service ();
            ~TH1Service ();
            void AddNewTH1 (const std::string& name, int nbin, double min, double max);
            void AddPlotFromFile (const std::string& name, const std::string& plotname, const std::string& filename);
            void Delete (const std::string& name);
            void Close ();
            plotmgr::ModifiedTH1<TH1Type>* GetPlot (const std::string& name) {return _th1set[name];} 
    
        private:
            bool _isdelete;
            std::map<std::string,plotmgr::ModifiedTH1<TH1Type>*> _th1set;
    };

}

#include "CMSSWUtility/Utils/src/TH1Service.ipp"

#endif
