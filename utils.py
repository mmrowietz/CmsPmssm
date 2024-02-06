from ROOT import *
from array import array

tl = TLatex()
tl.SetNDC()
cmsTextFont = 61
extraTextFont = 52
lumiTextSize = 0.6
lumiTextOffset = 0.2
cmsTextSize = 0.75
cmsTextOffset = 0.1
regularfont = 42
originalfont = tl.GetTextFont()
epsi = "#scale[1.3]{#font[122]{e}}"


def mkhistlogx(name, title, nbins, xmin, xmax,logx=True):
    if logx:
        logxmin = TMath.Log10(xmin)
        logxmax = TMath.Log10(xmax)
    else:
        logxmin=xmin
        logxmax=xmax
    binwidth = (logxmax-logxmin)/nbins
    xbins = array('d',[0]*(nbins+1))##might need to be defined out as 0's
    #xbins[0] = TMath.Power(10,logxmin)#xmin
    for i in range(0,nbins+1):
        if logx:
            xbins[i] = xmin + TMath.Power(10,logxmin+i*binwidth)
        else:
            xbins[i]= xmin + i*binwidth

#    print ('xbins', xbins )       
    h = TH1F(name,title,nbins,xbins);
    return h
def mkhistlogxy(name, title, nbinsx, xmin, xmax,nbinsy,ymin,ymax,logx=True,logy=True):
    if logx:
        logxmin = TMath.Log10(xmin)
        logxmax = TMath.Log10(xmax)
    else:
        logxmin=xmin
        logxmax=xmax
    if logy:
        logymin = TMath.Log10(ymin)
        logymax = TMath.Log10(ymax)
    else:
        logymin=ymin
        logymax=ymax
    binwidthx = float(logxmax-logxmin)/nbinsx
    binwidthy = float(logymax-logymin)/nbinsy
    xbins = array('d',[0]*(nbinsx+1))##might need to be defined out as 0's
    ybins = array('d',[0]*(nbinsy+1))##might need to be defined out as 0's
    #xbins[0] = TMath.Power(10,logxmin)#xmin
    for i in range(0,nbinsx+1):
        if logx:
            xbins[i] = xmin + TMath.Power(10,logxmin+i*binwidthx)
        else:
            xbins[i]= xmin + i*binwidthx
    for i in range(0,nbinsy+1):
        if logy:
            ybins[i] = ymin + TMath.Power(10,logymin+i*binwidthy)
        else:
            ybins[i] = ymin + i*binwidthy
#    print 'xbins', xbins[0],xbins[-1]
#    print 'ybins', ybins        
    h = TH2F(name,title,nbinsx,xbins,nbinsy,ybins);
    return h
def mkhistlogxyz(name, title, nbinsx, xmin, xmax,nbinsy,ymin,ymax,nbinsz,zmin,zmax,logx=True,logy=True,logz=True):
    if logx:
        logxmin = TMath.Log10(xmin)
        logxmax = TMath.Log10(xmax)
    else:
        logxmin=xmin
        logxmax=xmax
    if logy:
        logymin = TMath.Log10(ymin)
        logymax = TMath.Log10(ymax)
    else:
        logymin=ymin
        logymax=ymax
    if logz:
        logzmin = TMath.Log10(zmin)
        logzmax = TMath.Log10(zmax)
    else:
        logzmin=zmin
        logzmax=zmax
    binwidthx = float(logxmax-logxmin)/nbinsx
    binwidthy = float(logymax-logymin)/nbinsy
    binwidthz = float(logzmax-logzmin)/nbinsz
    xbins = array('d',[0]*(nbinsx+1))##might need to be defined out as 0's
    ybins = array('d',[0]*(nbinsy+1))##might need to be defined out as 0's
    zbins = array('d',[0]*(nbinsz+1))##might need to be defined out as 0's
    #xbins[0] = TMath.Power(10,logxmin)#xmin
    for i in range(0,nbinsx+1):
        if logx:
            xbins[i] = xmin + TMath.Power(10,logxmin+i*binwidthx)
        else:
            xbins[i]= xmin + i*binwidthx
    for i in range(0,nbinsy+1):
        if logy:
            ybins[i] = ymin + TMath.Power(10,logymin+i*binwidthy)
        else:
            ybins[i] = ymin + i*binwidthy
    for i in range(0,nbinsz+1):
        if logz:
            zbins[i] = zmin + TMath.Power(10,logzmin+i*binwidthz)
        else:
            zbins[i] = zmin + i*binwidthz
#    print 'xbins', xbins[0],xbins[-1]
#    print 'ybins', ybins        
    h = TH3F(name,title,nbinsx,xbins,nbinsy,ybins,nbinsz,zbins);
    return h

def histoStyler(h,color = kBlue,fill = False,linestyle = 1,linewidth = 3,fillstyle = 3009,markerstyle = 1,markersize = 1):
    h.SetLineWidth(linewidth)
    h.SetLineColor(color)
    h.SetMarkerColor(color)
    h.SetMarkerStyle(markerstyle)
    h.SetMarkerSize(markersize)
    h.SetLineStyle(linestyle)
    if fill:
        h.SetFillColor(color)
        h.SetFillStyle(fillstyle)
    size = 0.045
    titlesize = 0.055
    font = 132
    h.GetXaxis().SetLabelFont(font)
    h.GetYaxis().SetLabelFont(font)
    h.GetXaxis().SetTitleFont(font)
    h.GetYaxis().SetTitleFont(font)
    h.GetYaxis().SetTitleSize(titlesize)
    h.GetXaxis().SetTitleSize(titlesize)
    h.GetXaxis().SetLabelSize(size)   
    h.GetYaxis().SetLabelSize(size)
    h.GetXaxis().SetTitleOffset(1.0)
    h.GetYaxis().SetTitleOffset(1.2)
    h.GetZaxis().SetLabelFont(font)
    h.GetZaxis().SetTitleFont(font)
    h.GetZaxis().SetTitleSize(titlesize)
    h.GetZaxis().SetLabelSize(size)   
    h.GetZaxis().SetTitleOffset(0.9)
    
    h.Sumw2()

def graphStyler(g,color,width = 2,mstyle = 8):
    g.SetLineWidth(width)
    g.SetMarkerSize(width)
    g.SetMarkerStyle(mstyle)
    g.SetLineColor(color)
    g.SetMarkerColor(color)
    #g.SetFillColor(color)
    size = 0.055
    font = 132
    g.GetXaxis().SetLabelFont(font)
    g.GetYaxis().SetLabelFont(font)
    g.GetXaxis().SetTitleFont(font)
    g.GetYaxis().SetTitleFont(font)
    g.GetYaxis().SetTitleSize(size)
    g.GetXaxis().SetTitleSize(size)
    g.GetXaxis().SetLabelSize(size)   
    g.GetYaxis().SetLabelSize(size)
    g.GetXaxis().SetTitleOffset(1.0)
    g.GetYaxis().SetTitleOffset(1.05)
    
#def mkcanvas(name,left=0.14,right=False,top=0.22,bottom=0.15):
def mkcanvas(name,left=0.14,right=False,top=0.02,bottom=0.15):
    c1 = TCanvas(name,name,700,630)
    
    c1.SetBottomMargin(bottom)
    c1.SetLeftMargin(left)
    c1.SetTopMargin(top)
    if right:
        c1.SetRightMargin(right)
    else:
        pass
#        c1.SetRightMargin(.04)
    return c1

def mkcanvas_wide(name):
    c1 = TCanvas(name,name,1200,700)
    c1.Divide(2,1)
    c1.GetPad(1).SetBottomMargin(.14)
    c1.GetPad(1).SetLeftMargin(.14)
    c1.GetPad(2).SetBottomMargin(.14)
    c1.GetPad(2).SetLeftMargin(.14)    
    c1.GetPad(1).SetGridx()
    c1.GetPad(1).SetGridy()
    c1.GetPad(2).SetGridx()
    c1.GetPad(2).SetGridy()    
    #c1.SetTopMargin(.13)
    #c1.SetRightMargin(.04)
    return c1

def mklegend(x1=.27, y1=.72, x2=.74, y2=.88, color=kWhite):
    lg = TLegend(x1, y1, x2, y2)
    lg.SetFillColor(color)
    lg.SetTextFont(42)
    lg.SetBorderSize(0)
    lg.SetShadowColor(kWhite)
    lg.SetFillStyle(0)
    lg.SetEntrySeparation(0.33)
    return lg


def namewizard(name):
    if 'Mht' in name:
        return 'Offline H_{T}^{miss} [GeV]'
    if 'Met' in name:
        return 'Offline E_{T}^{miss} [GeV]'
    if 'Ht' in name:
        return 'Offline HT [GeV]'
    return name



def mkEfficiencies(hPassList, hAllList):
    gEffList = []
    for i in range(len(hPassList)):
        hPassList[i].Sumw2()
        hAllList[i].Sumw2()
        g = TGraphAsymmErrors(hPassList[i],hAllList[i],'cp')
        FixEfficiency(g,hPassList[i])
        g.SetMarkerSize(3)
        gEffList.append(g)
    return gEffList

def mkEfficiencyRatio(hPassList, hAllList,hName = 'hRatio'):#for weighted MC, you need TEfficiency!
    hEffList = []
    for i in range(len(hPassList)):
        hPassList[i].Sumw2()
        hAllList[i].Sumw2()    
        g = TGraphAsymmErrors(hPassList[i],hAllList[i],'cp')
        print ('RATIO........')
        FixEfficiency(g,hPassList[i])
        hEffList.append(hPassList[i].Clone('hEff'+str(i)))
        hEffList[-1].Divide(hAllList[i])
        cSam1 = TCanvas('cSam1')
        print ('this is the simply divided histogram:')
        hEffList[-1].Draw()
        cSam1.Update()

        print ('now putting in the uncertainties under ratio')
        for ibin in range(1,hEffList[-1].GetXaxis().GetNbins()+1):
            print ('setting errory(ibin)=',ibin,g.GetX()[ibin],g.GetErrorY(ibin))
            print ('compared with histo',ibin)
            hEffList[-1].SetBinError(ibin,1*g.GetErrorY(ibin-1))
            print ('errory(ibin)=',g.GetX()[ibin],g.GetErrorY(ibin-1))
        #histoStyler(hEffList[-1],hPassList[i].GetLineColor())

        cSam2 = TCanvas('cSam2')
        print ('this is the after divided histogram:')
        hEffList[-1].Draw()
        cSam2.Update()


        hEffList[-1].Draw()
    hRatio = hEffList[0].Clone(hName)
    hRatio.Divide(hEffList[1])
    hRatio.GetYaxis().SetRangeUser(0.95,1.05)
    c3 = TCanvas()
    hRatio.Draw()
    c3.Update()
    return hRatio


def pause(str_='push enter key when ready'):
        import sys
        print (str_)
        sys.stdout.flush() 
        raw_input('')

datamc = 'MC'
def stamp(lumi = 35.9):    
    tl.SetTextFont(cmsTextFont)
    tl.SetTextSize(1.2*tl.GetTextSize())
    tl.DrawLatex(0.155,0.93, 'CMS')
    tl.SetTextFont(extraTextFont)
    tl.SetTextSize(1.0/1.2*tl.GetTextSize())
    xlab = 0.235
    tl.DrawLatex(xlab,0.93, ('MC' in datamc)*' simulation '+'private')
    tl.SetTextFont(regularfont)
    tl.DrawLatex(0.68,0.93,'#sqrt{s} = 13 TeV L = '+str(lumi)+' fb^{-1}')

#------------------------------------------------------------------------------
def mkcdf(hist, minbin=1):
    hist.Scale(1.0/hist.Integral(1,hist.GetXaxis().GetNbins()))
    c = [0.0]*(hist.GetNbinsX()-minbin+2+1)
    j=1
    for ibin in xrange(minbin, hist.GetNbinsX()+1):
        c[j] = c[j-1] + hist.GetBinContent(ibin)
        j += 1
    c[j] = hist.Integral()
    return c

def mkroc(name, hsig, hbkg, lcolor=kBlue, lwidth=2, ndivx=505, ndivy=505):
    from array import array
    csig = mkcdf(hsig)
    cbkg = mkcdf(hbkg)
    npts = len(csig)
    esig = array('d')
    ebkg = array('d')
    for i in xrange(npts):
        esig.append(1 - csig[npts-1-i])
        ebkg.append(1 - cbkg[npts-1-i])
    g = TGraph(npts,esig,ebkg)
    g.SetName(name)
    g.SetLineColor(lcolor)
    g.SetLineWidth(lwidth)

    g.GetXaxis().SetTitle("#epsilon_{s}")
    g.GetXaxis().SetLimits(0,1)

    g.GetYaxis().SetTitle("#epsilon_{b}")
    g.GetHistogram().SetAxisRange(0,1, "Y");

    g.GetHistogram().SetNdivisions(ndivx, "X")
    g.GetHistogram().SetNdivisions(ndivy, "Y")
    return g


    
def calcTrackIso(trk, tracks):
    ptsum =  -trk.pt()
    for track in tracks:
        dR = TMath.Sqrt( (trk.eta()-track.eta())**2 + (trk.phi()-track.phi())**2)
        if dR<0.3: ptsum+=track.pt()
    return ptsum/trk.pt()

def calcTrackJetIso(trk, jets):
    for jet in jets:
        if not jet.pt()>30: continue
        if  TMath.Sqrt( (trk.eta()-jet.eta())**2 + (trk.phi()-jet.phi())**2)<0.5: return False
    return True

def calcMiniIso(trk, tracks):
    pt = trk.pt()
    ptsum = -pt
    if pt<=50: R = 0.2
    elif pt<=200: R = 10.0/pt
    else: R = 0.05
    for track in tracks:
        dR = TMath.Sqrt( (trk.eta()-track.eta())**2 + (trk.phi()-track.phi())**2)
        if dR<R: ptsum+=track.pt()
    return ptsum/trk.pt()
