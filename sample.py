import numpy as np
from obs_dwarf_properties import *

### This sample code generates density profile parameters r_s, rho_s, r_t

### Sample dwarf galaxy we consider
dwarf = 'UMa_II'

### Generate the parameters for Vpeak-14 galaxy formation model
rs,rhos,rt = dwarf_density_profile_MC(dwarf, galform='V50-10.5')

### Generate the parameters for log-unform prior case
rs_flat, rhos_flat = dwarf_density_profile_flatprior_MC(dwarf)


print(rs/kpc,rhos/(Msun/pc**3),rt/kpc)
print(rs_flat/kpc,rhos_flat/(Msun/pc**3))
