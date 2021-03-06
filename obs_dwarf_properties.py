import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.special import erf
from astropy.io import ascii

GeV    = 1.0                        # Unit of energy: GeV
eV     = GeV/1.0e9
keV    = 1.0e3*eV
MeV    = 1.0e3*keV
TeV    = 1.0e3*GeV
erg    = TeV/1.602                  # erg
J      = 1.0e7*erg                  # joule

cm     = 5.0678e4/eV                # centi-meter
m      = 1.0e2*cm
km     = 1.0e3*m

pc     = 3.086e18*cm                # persec
kpc    = 1.0e3*pc
Mpc    = 1.0e3*kpc
s      = 2.9979e10*cm               # second

kg     = J/m**2*s**2
Msun   = 1.989e30*kg                # Mass of the Sun
G      = 6.674e-11*m**3/kg/s**2     # Gravitational constant
deg    = np.pi/180.0                # Degree
arcmin = deg/60.                    # Arcminute
arcsec = arcmin/60.                 # Arcsecond



def dwarf_density_profile_MC(name, N_MC=10000, galform='Vpeak-14'):
    """
    Input:  name of dwarf, numbre of Monte Carlo, galaxy formation model
    Output: r_s [kpc], rho_s [Msun/pc^3], r_t [kpc], each as a numpy array generated by Monte Carlo simulations

    Names should be chosen from the following.
    Classicals: Carina, Draco, Fornax, Leo_I, Leo_II, Sagittarius, Sculptor, Sextans, UMi
    Ultrafaints: Aquarius_2, Bootes_I, Bootes_II, CVn_I, CVn_II, Carina_II, ComBer, Draco_II, Eridanus_II, Grus_I, Hercules, Horologium_I, Hyrdus_1, Leo_IV, Leo_T, Leo_V, Pegasus_III, Pisces_II, Reticulum_II, Segue_1, Segue_2, Triangulum_II, Tucana_II, Tucana_III, UMa_I, UMa_II, Willman_1

    Galaxy formation models should be chosen from the following.
    Classicals: Classical
    Utrafaints: V50-10.5 (default), several others such as Vpeak-18, etc.

    N_MC is the number of Monte Carlo simulations.
    """

    m,rs,rhos,rt,w = obs_dwarf_properties(name,galform=galform)

    index    = np.arange(np.alen(m))
    cdf      = np.cumsum(w)/np.sum(w)
    index_MC = np.interp(np.random.rand(N_MC),cdf,index).astype(int)
    rs_MC    = rs[index_MC]
    rhos_MC  = rhos[index_MC]
    rt_MC    = rt[index_MC]

    return rs_MC, rhos_MC, rt_MC



def dwarf_density_profile_flatprior_MC(name, N_MC=100, N_rs=200, logrsmin=-3., logrsmax=2., cosmocut=True):
    """
    Input:  name of dwarf
    Output: r_s [kpc], rho_s [Msun/pc^3]

    The calculations will be done for log-uniform prior where the parameter space is uniformed surveyed for logrsmin < log(r_s/kpc) < logrsmax. One can implement the GS15 cut by turning "cosmocut" on.

    Names should be chosen from the following.
    Classicals: Carina, Draco, Fornax, Leo_I, Leo_II, Sagittarius, Sculptor, Sextans, UMi
    Ultrafaints: Aquarius_2, Bootes_I, Bootes_II, CVn_I, CVn_II, Carina_II, ComBer, Draco_II, Eridanus_II, Grus_I, Hercules, Horologium_I, Hyrdus_1, Leo_IV, Leo_T, Leo_V, Pegasus_III, Pisces_II, Reticulum_II, Segue_1, Segue_2, Triangulum_II, Tucana_II, Tucana_III, UMa_I, UMa_II, Willman_1

    Number of Monte Carlo can be adjusted by tuning N_MC to different values.
    """

    rhalf,sigma_rhalf,sigmalos,sigma_sigmalos,dist,sigma_dist = rhalf_sigmalos(name)
    rhalf_MC_temp = np.random.normal(loc=rhalf,scale=sigma_rhalf,size=N_MC)
    vdisp_MC_temp = np.random.normal(loc=sigmalos,scale=sigma_sigmalos,size=N_MC)
    rhalf_MC = rhalf_MC_temp[(rhalf_MC_temp>0.)*(vdisp_MC_temp>0.)]
    vdisp_MC = vdisp_MC_temp[(rhalf_MC_temp>0.)*(vdisp_MC_temp>0.)]

    rs = np.logspace(logrsmin,logrsmax,N_rs)*kpc
    rs = rs.reshape(N_rs,1)
    rhos = vdisp_MC**2*3./(4.*np.pi*G*rs*rhalf_MC)
    rhos = rhos/(myfunc1(100.,rhalf_MC/rs)-myfunc1(0.,rhalf_MC/rs))
    rs     = rs*np.ones((1,np.alen(vdisp_MC)))
    rs     = rs.reshape(N_rs*np.alen(vdisp_MC))
    rhos   = rhos.reshape(N_rs*np.alen(vdisp_MC))
    weight = np.ones(np.alen(rs))

    if(cosmocut==True):
        cutdata = np.loadtxt('data/cosmocut_rhosthreshold.txt')
        rs_data = cutdata[:,0]*kpc
        rhos_data = cutdata[:,1]*Msun/pc**3
        logrhos_th = np.interp(np.log10(rs),np.log10(rs_data),np.log10(rhos_data))
        cond = rhos<10.**logrhos_th
        rs = rs[cond]
        rhos = rhos[cond]
        weight = weight[cond]

    return rs, rhos



def obs_dwarf_properties(name, N_herm_rhalf=10, N_herm_vdisp=20, galform='V50-10.5'):
    subhalo_data = np.load('data/subhalo_params_1e12_1e5.npy')
    ma200        = subhalo_data[:,0]*Msun
    za0          = subhalo_data[:,1]
    ma0          = Mvir_from_M200_fit(ma200,za0)
    rs_a         = subhalo_data[:,2]*kpc
    rhos_a       = subhalo_data[:,3]*Msun/pc**3
    m0           = subhalo_data[:,4]*Msun
    rs0          = subhalo_data[:,5]*kpc
    rhos0        = subhalo_data[:,6]*Msun/pc**3
    ct0          = subhalo_data[:,7]
    rt0          = ct0*rs0
    B_a          = subhalo_data[:,8]
    B_0          = subhalo_data[:,9]
    fsub_a       = subhalo_data[:,10]
    fsub0        = subhalo_data[:,11]
    weight       = subhalo_data[:,12]

    if(galform!=None):
        Vmax_a = np.sqrt(4.*np.pi*G*rhos_a/4.625)*rs_a
        if(galform=='Vpeak-22'):
            galform_cond = (Vmax_a>22.*km/s)*(Vmax_a<30.*km/s)
        elif(galform=='Vpeak-20'):
            galform_cond = (Vmax_a>20.*km/s)*(Vmax_a<30.*km/s)
        elif(galform=='Vpeak-18'):
            galform_cond = (Vmax_a>18.*km/s)*(Vmax_a<30.*km/s)
        elif(galform=='Vpeak-16'):
            galform_cond = (Vmax_a>16.*km/s)*(Vmax_a<30.*km/s)
        elif(galform=='Vpeak-14'):
            galform_cond = (Vmax_a>14.*km/s)*(Vmax_a<30.*km/s)
        elif(galform=='Vpeak-12'):
            galform_cond = (Vmax_a>12.*km/s)*(Vmax_a<30.*km/s)
        elif(galform=='Vpeak-6'):
            galform_cond = (Vmax_a>6.*km/s)*(Vmax_a<30.*km/s)
        elif(galform=='V50-18'):
            V50          = 18.*km/s
            sigma        = 2.5*km/s
            fgal         = 1./2.*(1.+erf((Vmax_a-V50)/(np.sqrt(2.)*sigma)))
            weight       = weight*fgal
            galform_cond = Vmax_a<30.*km/s
        elif(galform=='V50-10.5'):
            V50          = 10.5*km/s
            sigma        = 2.5*km/s
            fgal         = 1./2.*(1.+erf((Vmax_a-V50)/(np.sqrt(2.)*sigma)))
            weight       = weight*fgal
            galform_cond = Vmax_a<30.*km/s
        elif(galform=='Classical'):
            galform_cond = Vmax_a>25.*km/s
        ma200  = ma200[galform_cond]
        za0    = za0[galform_cond]
        ma0    = ma0[galform_cond]
        rs_a   = rs_a[galform_cond]
        rhos_a = rhos_a[galform_cond]
        m0     = m0[galform_cond]
        rs0    = rs0[galform_cond]
        rhos0  = rhos0[galform_cond]
        ct0    = ct0[galform_cond]
        rt0    = rt0[galform_cond]
        B_a    = B_a[galform_cond]
        B_0    = B_0[galform_cond]
        fsub_a = fsub_a[galform_cond]
        fsub0  = fsub0[galform_cond]
        weight = weight[galform_cond]

    rhalf0,sigma_rhalf,vdisp0,sigma_vdisp,dist,sigma_dist = rhalf_sigmalos(name)
    x1,w1    = hermgauss(N_herm_rhalf)
    rhalf    = np.sqrt(2.)*sigma_rhalf*x1+rhalf0
    w1       = w1[rhalf>0.]
    rhalf    = rhalf[rhalf>0.]
    rhalf    = rhalf.reshape(np.alen(rhalf),1)
    w1       = w1.reshape(np.alen(w1),1)
    vdisp_sq = 4.*np.pi*G*rs0*rhalf*rhos0/3.
    vdisp_sq = vdisp_sq*(myfunc1(100.,rhalf/rs0)-myfunc1(0.,rhalf/rs0))
    vdisp_th = np.sqrt(vdisp_sq)
    chi2     = ((vdisp_th-vdisp0)/sigma_vdisp)**2
    like     = np.exp(-chi2/2.)
    like     = np.sum(like*w1/np.sqrt(np.pi),axis=0)
    weight   = weight*like

    return m0[weight>0.], rs0[weight>0.], rhos0[weight>0.], rt0[weight>0.], weight[weight>0.]



def rhalf_sigmalos(name):
    dwarfdata                  = ascii.read('data/dwarfdata_circularized2.txt')
    list_name                  = np.array(dwarfdata['col1'])
    list_dist                  = np.array(dwarfdata['col2'])*kpc
    list_rhalf_plummer         = np.array(dwarfdata['col3'])*arcmin
    list_error_rhalf_plummer_l = np.array(dwarfdata['col4'])*arcmin
    list_error_rhalf_plummer_u = np.array(dwarfdata['col5'])*arcmin
    list_rhalf_exp             = np.array(dwarfdata['col6'])*arcmin
    list_error_rhalf_exp_l     = np.array(dwarfdata['col7'])*arcmin
    list_error_rhalf_exp_u     = np.array(dwarfdata['col8'])*arcmin
    list_vdisp                 = np.array(dwarfdata['col9'])*km/s
    list_error_vdisp_l         = np.array(dwarfdata['col10'])*km/s
    list_error_vdisp_u         = np.array(dwarfdata['col11'])*km/s
    list_vdisp_ul              = np.array(dwarfdata['col12'])*km/s
    list_error_rhalf_plummer   = (list_error_rhalf_plummer_l+list_error_rhalf_plummer_u)/2.
    list_error_rhalf_exp       = (list_error_rhalf_exp_l+list_error_rhalf_exp_u)/2.
    list_error_vdisp           = (list_error_vdisp_l+list_error_vdisp_u)/2.

    i                  = np.argwhere(list_name==name)[0][0]
    dist               = list_dist[i]
    sigma_dist         = 0.
    rhalf              = list_rhalf_plummer[i]*dist
    sigma_rhalf        = list_error_rhalf_plummer[i]*dist
    if(np.isnan(rhalf)==True):
        rhalf          = list_rhalf_exp[i]*dist
        sigma_rhalf    = list_error_rhalf_exp[i]*dist
    sigmalos           = list_vdisp[i]
    sigma_sigmalos     = list_error_vdisp[i]
    if(np.isnan(sigmalos)==True):
        #sigmalos       = 0.
        #sigma_sigmalos = list_vdisp_ul[i]/2.
        dwarfdata2 = ascii.read('data/vdispupperlimits.txt')
        list_name2          = np.array(dwarfdata2['col1'])
        list_sigmalos       = np.array(dwarfdata2['col2'])*km/s
        list_sigma_sigmalos = np.array(dwarfdata2['col3'])*km/s
        sigmalos            = list_sigmalos[list_name2==name]
        sigma_sigmalos      = list_sigma_sigmalos[list_name2==name]

    return rhalf, sigma_rhalf, sigmalos, sigma_sigmalos, dist, sigma_dist



def Mvir_from_M200_fit(M200, z):

    def Omegaz(p,x):
        E=p[0]*pow(1+x,3)+p[1]*pow(1+x,2)+p[2]
        return p[0]*pow(1+x,3)*pow(E,-1)

    def Delc(x):
        return 18*pow(np.pi,2)+(82*x)-39*pow(x,2)

    a1 = 0.5116
    a2 = -0.4283
    a3 = -3.13e-3
    a4 = -3.52e-5
    OmegaL = 0.692
    OmegaC = 0.25793
    OmegaB = 0.049150
    Omegar = 0.0
    pOmega = [OmegaC+OmegaB,Omegar,OmegaL]
    Oz=Omegaz(pOmega,z)
    def ffunc(x):
        return np.power(x,3.0)*(np.log(1.0+1.0/x)-1.0/(1.0+x))
    def xfunc(f):
        p = a2 + a3*np.log(f) + a4*np.power(np.log(f),2.0)
        return np.power(a1*np.power(f,2.0*p)+(3.0/4.0)**2,-0.5)+2.0*f
    return Delc(Oz-1)/200.0*M200 \
        *np.power(conc200(M200,z)*xfunc(Delc(Oz-1)/200.0*ffunc(1.0/conc200(M200,z))),-3.0)


def conc200(M200,z):
    alpha_cMz_1=1.7543-0.2766*(1+z)+0.02039*pow(1+z,2)
    beta_cMz_1=0.2753+0.00351*(1+z)-0.3038*pow(1+z,0.0269)
    gamma_cMz_1=-0.01537+0.02102*pow(1+z,-0.1475)
    c_Mz_1=pow(10,alpha_cMz_1+beta_cMz_1*np.log10(M200/Msun) \
               *(1+gamma_cMz_1*pow(np.log10(M200/Msun),2)))
    alpha_cMz_2=1.3081-0.1078*(1+z)+0.00398*pow(1+z,2)
    beta_cMz_2=0.0223-0.0944*pow(1+z,-0.3907)
    c_Mz_2=pow(10,alpha_cMz_2+beta_cMz_2*np.log10(M200/Msun))
    return np.where(z<=4,c_Mz_1,c_Mz_2)


def myfunc1(x, c):
    output = ((-1.+c*(x+c*(2.+x*(c+3.*x)))) \
        /((1.+c**2)**2*(1.+c*x)*np.sqrt(1.+x**2)) \
        +(c*(-2.+c**2)*(np.log(1.+c*x) \
        -np.log(c-x+np.sqrt(1.+c**2)*np.sqrt(1.+x**2)))) \
        /(1.+c**2)**(5./2.))
    return output


def Distance (dwarf):
    if (dwarf == 'Carina'):
        Dis = 105.*kpc
    elif (dwarf == 'Draco'):
        Dis = 76.*kpc
    elif (dwarf == 'Fornax'):
        Dis = 147.*kpc
    elif (dwarf == 'Leo_I'):
        Dis = 254.*kpc
    elif (dwarf == 'Leo_II'):
        Dis = 233.*kpc
    elif (dwarf == 'Sagittarius'):
        Dis = 26.*kpc
    elif (dwarf == 'Sculptor'):
        Dis = 86.*kpc
    elif (dwarf == 'Sextans'):
        Dis = 86.*kpc
    elif (dwarf == 'UMi'):
        Dis = 76.*kpc
    elif (dwarf == 'Aquarius_2'):
        Dis = 107.9*kpc
    elif (dwarf == 'Bootes_I'):
        Dis = 66.*kpc
    elif (dwarf == 'Bootes_II'):
        Dis = 42.*kpc
    elif (dwarf == 'CVn_I'):
        Dis = 218.*kpc
    elif (dwarf == 'CVn_II'):
        Dis = 160.*kpc
    elif (dwarf == 'Carina_II'):
        Dis = 36.2*kpc
    elif (dwarf == 'ComBer'):
        Dis = 44.*kpc
    elif (dwarf == 'Draco_II'):
        Dis = 20.*kpc
    elif (dwarf == 'Eridanus_II'):
        Dis = 380.*kpc
    elif (dwarf == 'Grus_I'):
        Dis = 120.*kpc
    elif (dwarf == 'Hercules'):
        Dis = 132.*kpc
    elif (dwarf == 'Horologium_I'):
        Dis = 79.*kpc
    elif (dwarf == 'Hyrdus_1'):
        Dis = 27.6*kpc
    elif (dwarf == 'Leo_IV'):
        Dis = 154.*kpc
    elif (dwarf == 'Leo_T'):
        Dis = 417.*kpc
    elif (dwarf == 'Leo_V'):
        Dis = 178.*kpc
    elif (dwarf == 'Pegasus_III'):
        Dis = 215.*kpc
    elif (dwarf == 'Pisces_II'):
        Dis = 182.*kpc
    elif (dwarf == 'Reticulum_II'):
        Dis = 30.*kpc
    elif (dwarf == 'Segue_1'):
        Dis = 23.*kpc
    elif (dwarf == 'Segue_2'):
        Dis = 35.*kpc
    elif (dwarf == 'Triangulum_II'):
        Dis = 30.*kpc
    elif (dwarf == 'Tucana_II'):
        Dis = 57.*kpc
    elif (dwarf == 'Tucana_III'):
        Dis = 25.*kpc
    elif (dwarf == 'UMa_I'):
        Dis = 97.*kpc
    elif (dwarf == 'UMa_II'):
        Dis = 32.*kpc
    elif (dwarf == 'Willman_1'):
        Dis = 38.*kpc

    return Dis
