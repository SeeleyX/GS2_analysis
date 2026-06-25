def densityCalc(Zeff, Zimp):

    '''
    Calculate the densities of a Hydrogen and Impurity based on the effective 
    charge of the plasma, Zeff and the charge of the ionised impurity Zimp.

    Normalised by a single elctron. 
    '''

    nimp = (Zeff - 1)/(Zimp*(Zimp - 1)) # Effective charge eq
    nfuel = 1 - Zimp*nimp               # Quasineutrality eq

    print(f'Impurity density: {nimp:.5f}')
    print(f'Fuel density: {nfuel:.5f}')

    return (nimp, nfuel)

#Effective charge of 3
Zeff = 2.5

#carbon
Zc = 6 
densityCalc(Zeff, Zc)