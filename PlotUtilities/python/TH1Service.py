from CMSSWUtility.Utils.ModifiedTH1 import ModifiedTH1
import ROOT

class TH1Service:

    def __init__(self):
        self.th1_set = dict()

    def addNewTH1(self, name, nbin, xmin, xmax):
        self.th1_set[name] = ModifiedTH1(None, name, nbin, xmin, xmax)

    def addPlotFromFile(self, name, plotname, filename):

        file = ROOT.TFile(filename)

        if file.IsZombie():
            self.close()
            raise IOError('%s can not be found!' % filename)

        plot = file.Get(plotname)
        plot.SetDirectory(0)
        file.Close()
        self.th1_set[name] = ModifiedTH1(plot)

    def getPlot(self, name):
        return self.th1_set[name]

    def delete(self, name):
        self.th1_set[name].close()
        del self.th1_set[name]

    def close(self):
        for name in self.th1_set.keys():
            self.th1_set[name].close()
        self.th1_set.clear()
