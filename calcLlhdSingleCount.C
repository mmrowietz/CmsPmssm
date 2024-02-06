#include "TMath.h"
#include "TF1.h"
#include "TF2.h"
#include "TGraph.h"
#include "TH2D.h"
#include "TH1D.h"
#include "TCanvas.h"
#include "TPaveText.h"
#include "TString.h"

#include "Math/Integrator.h"
#include "Math/IntegratorMultiDim.h"
#include "Math/WrappedTF1.h"
#include "Math/WrappedMultiTF1.h"
#include "Math/AllIntegrationTypes.h"
#include "Math/GaussLegendreIntegrator.h"
#include "Math/GSLIntegrator.h"
 

#include "iostream"

double logPoisson(double N,double n){
  return N*TMath::Log(n) - n - (N > 0 ? TMath::LnGamma(N+1) : 0);
}

double logGammaFunc(double X,double alpha,double beta){
  return alpha*TMath::Log(beta) + (alpha-1)*TMath::Log(X) -X*beta - TMath::LnGamma(alpha);
}

double integrand(int N,double b,double s,double alpha,double beta){
  double res1 = logPoisson(N,b+s);
  double res2 = logGammaFunc(b,alpha,beta);
  return(TMath::Exp(res1 + res2));
}

void setAlphaBeta(double B,double dB,double & alpha,double & beta){
  double B2 = B*B;
  double dB2 = dB*dB;
  alpha = (B2 + B*TMath::Sqrt(B2 + 4.*dB2) + 2.*dB2)/2./dB2;
  beta = (B + TMath::Sqrt(B2 + 4.*dB2))/2./dB2;
}

double lhd(double N,double s,double B,double dB){
  double alpha,beta;
  setAlphaBeta(B,dB,alpha,beta);
  double minb = 0;
  double maxb = max(B + 5*dB,N+5*dB);
  TF1 f("integrand","integrand([0],x,[1],[2],[3])",minb,maxb);
  f.SetParameter(0,N);
  f.SetParameter(1,s);
  f.SetParameter(2,alpha);
  f.SetParameter(3,beta);
  ROOT::Math::WrappedTF1 wf(f);
  ROOT::Math::Integrator ig(wf,ROOT::Math::IntegrationOneDim::kGAUSS);
  double res = ig.Integral(minb,maxb);
  return res;
}

double llhd(double N,double s,double B,double dB){
  return TMath::Log(lhd(N,s,B,dB));
}

double llhdAna(double N,double s,double B,double dB){
  double alpha,beta;
  setAlphaBeta(B,dB,alpha,beta);
  double x = 1.0/(1.+beta);
  double a = beta*x;
  double sum = 0;

  if(alpha > 1.){
    double _alpha = N+1+1;
    double _beta = alpha - 1.;
    double exponent = 0;
    
    for(int r = 0;r<=N;++r){
      _alpha -= 1;
      // log f(x;alpha,beta) with f the beta distribution
      exponent = TMath::LnGamma(_alpha + _beta) - TMath::LnGamma(_alpha) - TMath::LnGamma(_beta) 
	+ (_alpha -1)*TMath::Log(x) + (_beta -1)*TMath::Log(1 - x);
      sum += TMath::Exp(exponent)*TMath::Poisson(r,s);
    }
  }
  else{
    for(int r = 0;r<=N;++r)
      sum += TMath::Power(x, N-r)*TMath::Power(1-x, alpha-1.-1.)*TMath::Poisson(r,s);
  }
  return TMath::Log(a*a*sum);
}

double lhdAna(double N,double s,double B,double dB){
  return TMath::Exp(llhdAna(N,s,B,dB));
}

void graphLlhdAna(double N,double B,double dB){
  int nsteps = 100;
  double s_min = max(0.,N-B - 5*dB);
  double s_max = (N-B) + 5*dB;
  TGraph * g = new TGraph();
  for(double i =0;i<nsteps;i=i+1.){
    double s = s_min + i*(s_max - s_min)/nsteps;
    double _llhd = lhdAna(N,s,B,dB);
    g->SetPoint(i,s,_llhd);
  }
  g->Draw("al");
  TPaveText * box = new TPaveText(0.5,0.5,1.,1.,"NDC");
  stringstream str;
  str << "N = " << N;
  box->AddText(str.str().c_str());
  str.str("");
  str << "N-B = " << N-B;
  box->AddText(str.str().c_str());
  str.str("");
  str << "B = " << B << "+/-" << dB;
  box->AddText(str.str().c_str());
  box->Draw();
}


double integrand2D(double s, double N, double B,double dB,double S,double w){
  double res1 = lhdAna(N,s,B,dB);
  double res2 = TMath::Exp(logPoisson(S,s/w));
  return res1*res2;
}

double integrandReal2D(double b,double s, double N, double alpha,double beta,double S,double w){
  double res1 = integrand(N,b,0.,alpha,beta);
  //double res2 = TMath::Exp(logPoisson(S,s/w));
  double res2 = TMath::GammaDist(s,S+1,1./w);
  return res1*res2;
}

double lhd2D(double N,double B,double dB,double S,double w){
  

  double alpha,beta;
  setAlphaBeta(B,dB,alpha,beta);
 
  double alpha_s = S + 1;
  double beta_s = 1./w;
  
  double stdev_s = TMath::Sqrt(alpha_s)/beta_s;
  double mins = max(0.,S*w - 10*stdev_s);
  double maxs = S*w + 10*stdev_s;
  
  //maxs = 0;

  TF1 f("integrand","integrand2D(x,[0],[1],[2],[3],[4])",mins,maxs);
  f.SetParameter(0,N);
  f.SetParameter(1,B);
  f.SetParameter(2,dB);
  f.SetParameter(3,S);
  f.SetParameter(4,w);
  ROOT::Math::WrappedTF1 wf(f);
  ROOT::Math::GSLIntegrator ig(ROOT::Math::IntegrationOneDim::kADAPTIVE);
  ig.SetFunction(wf);
  double res = ig.Integral(mins,maxs);

  //cout << "-" << N << " " << B << " " << dB << " " << S << " " << w << " " << res << endl;

  return res;

}

double llhd2D(double N,double B,double dB,double S,double w){
  return TMath::Log(lhd2D(N,B,dB,S,w));
}



void test(){

  /*
  double N = 23;
  double B = 14.1;
  double dB = 2.8;
  double s = 6.47244;
  double S = 80.0;
  */

  /*
  double N = 34;
  double B = 19.3;
  double dB = 3.6;
  double s = 6.643065;
  double S = 5.5;
  */

  /*
  double N = 11;
  double B = 4.8;
  double dB = 1.5;
  double s = 1.328613;
  double S = 1.1;
  */

  double N = 9;
  double B = 5.7;
  double dB = 1.9;
  double s = 0.110604;
  double S = 1.0;

  double w = s/S;
  
  double _llhdAna_100 = llhdAna(N,s,B,dB);
  double _llhdAna_000 = llhdAna(N,0,B,dB);
  cout << "1D ana: " <<  _llhdAna_100 << " " << _llhdAna_000 << " " << _llhdAna_100 - _llhdAna_000 << endl;

  double _llhd_100 = llhd(N,s,B,dB);
  double _llhd_000 = llhd(N,0,B,dB);
  cout << "1D num: " <<  _llhd_100 << " " << _llhd_000 << " " << _llhd_100 - _llhd_000 << endl;
  
  double _llhd2D_100 = llhd2D(N,B,dB,S,w);
  double _llhd2D_000 = llhd2D(N,B,dB,0,w);
  cout << "2D    : " << _llhd2D_100 << " " << _llhd2D_000 << " " << _llhd2D_100 - _llhd2D_000 << endl;

}


void test2D(){

  double N = 11;
  double B = 4.8;
  double dB = 1.5;
  double S = 3;
  double w = 3;

  double mins =0;
  double maxs =50 ;

  TF1 * f = new TF1("integrand","integrand2D(x,[0],[1],[2],[3],[4])",mins,maxs);
  f->SetParameter(0,N);
  f->SetParameter(1,B);
  f->SetParameter(2,dB);
  f->SetParameter(3,S);
  f->SetParameter(4,w);
  f->Draw();
}
