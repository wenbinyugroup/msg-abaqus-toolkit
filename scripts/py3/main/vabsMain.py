from __future__ import print_function
from abaqus import *
from math import *
from datetime import *
import subprocess
from utils.utilities import *
from main.createVABSInputMain import *
from sgdataio.vabs import create_vabs_recovery_input
import os.path
# import codecs
import time


def VABSMain(
    recover_flag, gen_inp_only, vabs_inp_name='', abq_inp_name='',
    timoshenko_flag='', thermal_flag='', trapeze_flag='',
    vlasov_flag='', curve_flag='', k='', oblique_flag='', cos='',
    model_recover='', vabs_rec_name='', vabs_inp_name2='',
    u='', c='', sf='', sm='', df='', dm='',
    gamma='', kappa='', kappa_p='', trans_flag=None
):
    
    st = datetime.now()
    print(st.strftime("%m-%d-%Y %H:%M:%S"))

    if recover_flag == 1:

        vabs_input = createVABSInputMain(
            abq_inp_name, vabs_inp_name,
            timoshenko_flag, thermal_flag, trapeze_flag, vlasov_flag,
            curve_flag, k, oblique_flag, cos, trans_flag=trans_flag
        )

    elif recover_flag == 2:

        vabs_input = create_vabs_recovery_input(
            vabs_rec_name, vabs_inp_name2, model_recover,
            u, c, sf, sm, df, dm, gamma, kappa, kappa_p
        )

    print(vabs_input)

    if not gen_inp_only:
        print('Running VABS...')
        vabsTimeStart = time.perf_counter()
        result = subprocess.run(
            ['VABSIII', vabs_input], timeout=300, check=False
        )
        if result.returncode != 0:
            raise RuntimeError('VABS exited with code %d' % result.returncode)
        vabsTimeEnd = time.perf_counter()
        vabsTime = vabsTimeEnd - vabsTimeStart
        print('VABS TIME: ' + str(vabsTime))

    return 1



