# SETUP
# importing relevant modules
from psychopy import visual, event, core, gui, data, monitors
import random
import pandas as pd
import os
import os.path as op
from pylsl import StreamInfo, StreamOutlet
from time import sleep
import time
from random import randint

info = StreamInfo(name='backwardmasking', type='Markers', channel_count=1, channel_format='int32', source_id='backwardmasking_001')

outlet = StreamOutlet(info)  # Broadcast the stream.


# Marcadores
# 0: Comienza trial
# 1: Estimulo

# import parallel
# import matplotlib.pyplot as plt

# open parallel port
# parallel_port = parallel.Parallel()
# parallel_port.setData(0)

# Experiment session
exp_name = 'metacontrast'
exp_info = {'Participant': '',
            'Stim': ['A', 'B', 'C'],
            'Session': ['pre', 'dur', 'post']}
dlg = gui.DlgFromDict(dictionary=exp_info, title=exp_name)
if dlg.OK is False:
    core.quit()
exp_info['date'] = data.getDateStr()
exp_info['exp_name'] = exp_name

# Paths and filename
home_dir = 'C:\\Users\\Fede\\Desktop\\COCUCOGNITRON\\ConsciousAccess\\'
script_dir = op.join(home_dir, 'Scripts')
images_dir = op.join(home_dir, 'Images')
data_dir = op.join(home_dir, 'Data')
trial_dir = op.join(home_dir, 'Trial_list')
participant_dir = op.join(data_dir, '{}'.format(exp_info['Participant']))
if not op.exists(participant_dir):
    os.mkdir(participant_dir)
filename = op.join(participant_dir, '{}_{}_{}_{}_{}'.format(
    exp_info['Participant'],
    exp_name,
    exp_info['date'],
    exp_info['Stim'],
    exp_info['Session']))

#WINDOW
win = visual.Window([800, 800],
                    monitor='Dell precision',
                    fullscr=True,
                    screen=1,
                    units='norm',
                    color='gainsboro') #gainsboro


# Store frame rate of monitor if we can measure it
exp_info['frame_rate'] = win.getActualFrameRate()
if exp_info['frame_rate'] is not None:
    frameDur = 1.0 / round(exp_info['frame_rate']) #divide by actual refresh rate
else:
    frameDur = 1.0 / 60.0 #use 60 when we weren't able to get the actual refresh rate
exp_info['frame_dur'] = win.getMsPerFrame()

# Clocks & times
global_clock = core.Clock()
trial_clock = core.Clock()
obj_clock = core.Clock()

target_dur = 1  # ~ 16 ms
mask_dur = 15  # ~ 250 ms
ep_dur = 48  # ~ 800 ms

# Sending trigger and reseting objective clock
#def reset_clock_and_send_trigger(value):
#    parallel_port.setData(value)  # write the trigger values
#    obj_clock.reset()


# Stimuli

fixation = visual.SimpleImageStim(win=win,
                                  image=op.join(images_dir, 'cross_grey.tif'))
dotUR = visual.ImageStim(win=win,
                         image=op.join(images_dir, 'dot_grey.tif'),
                         size=0.02)
dotUL = visual.ImageStim(win=win,
                         image=op.join(images_dir, 'dot_grey.tif'),
                         size=0.02)
dotDR = visual.ImageStim(win=win,
                         image=op.join(images_dir, 'dot_grey.tif'),
                         size=0.02)
dotDL = visual.ImageStim(win=win,
                         image=op.join(images_dir, 'dot_grey.tif'),
                         size=0.02)

t7 = visual.TextStim(win=win, text='7',units='norm', height=0.15, color='black')

t2 = visual.TextStim(win=win, text='2',units='norm', height=0.15, color='black')

t8 = visual.TextStim(win=win, text='8',units='norm', height=0.15, color='black')

t3 = visual.TextStim(win=win, text='3',units='norm', height=0.15, color='black')

#TERGET KOY BURAYA
mask_image = visual.SimpleImageStim(win=win,
                                    image=op.join(images_dir, 'mask3_grey.tif'))

#'seen/not seen' is counterbalanced
scale_rating1 = visual.RatingScale(win=win,
                                   lineColor='black',
                                   # low=0, high=1,
                                   choices=['no visto', " ", 'visto'],
                                   markerStart=1,
                                   textColor='black',
                                   pos=(0, 0),
                                   noMouse=True,
                                   scale=None,
                                   marker='triangle',
                                   markerColor='DarkRed',
                                   showAccept=False,
                                   acceptKeys=['space', 'num_enter'])
scale_rating2 = visual.RatingScale(win=win,
                                   lineColor='black',
                                   # low=0, high=1,
                                   choices=['visto', " ", 'no visto'],
                                   markerStart=1,
                                   textColor='black',
                                   pos=(0, 0),
                                   noMouse=True,
                                   scale=None,
                                   marker='triangle',
                                   markerColor='DarkRed',
                                   showAccept=False,
                                   acceptKeys=['space', 'num_enter'])

# Trials
trial_list_df = pd.read_excel(op.join(trial_dir, "trial_list_final.xlsx"))
trial_list_df = trial_list_df.fillna(0)
trial_list_df = trial_list_df.replace(to_replace=0, value='')

#order of trials
order = []
for i in range(len(trial_list_df)):  # len(trial_list_df)):
    order.append(i)

# data storage
col_participant = []
col_stim = []
col_session = []
col_block = []
col_order = []
col_frame_rate = []
col_frame_int = []
col_real_soa = []
col_positions = []
col_targets = []
col_masks = []
col_soas = []
col_answers = []
col_obj_rating = []
col_obj_RT = []
col_subj_rating = []
col_subj_RT = []
col_trial_dur = []
col_trigger = []
sumSOA = 0

# fixation cross & initializing clock
global_clock.reset()
fixation.draw()
win.flip()
core.wait(1)

# iteration over the randomised trial list
n_block = 4
n = 0
for i in range(n_block):
    random.shuffle(order) #random order of the trials

    for trial in order:
        #random order of rating
        r = random.randint(1, 2)
        if r == 1:
            scale_rating = scale_rating1
        else:
            scale_rating = scale_rating2
        # setting parameters for this trial
        soa_dur = int(trial_list_df.loc[trial]['SOA']) #row = trial, column = SOA
        dotUR.pos = (0.5, 0.5)
        dotUL.pos = (-0.5, 0.5)
        dotDR.pos = (0.5, -0.5)
        dotDL.pos = (-0.5, -0.5)
        stim=trial_list_df.loc[trial]['target']
        if stim=='2.tif':
            t=t2
            #t.pos=([trial_list_df.loc[trial]['position'], 0.0])
        if stim=='3.tif':
            t=t3
            #t.pos=([trial_list_df.loc[trial]['position'], 0.0])
        if stim=='7.tif':
            t=t7
            #t.pos=([trial_list_df.loc[trial]['position'], 0.0])
        if stim=='8.tif':
            t=t8
            #t.pos=([trial_list_df.loc[trial]['position'], 0.0])
        if stim=='blank.tiff':
            t= visual.TextStim(win=win, text=' ',units='norm', height=0.15, color='gainsboro')
        t.setPos([trial_list_df.loc[trial]['position'], 0.0]) #position of target
        t.contrast=-0.258 #determined with staircase
        mask_image.setPos(
            [trial_list_df.loc[trial]['position'], 0.0]) #same position for mask
        # mask_image.setImage(
        #     op.join(images_dir, trial_list_df.loc[trial]['mask']))
        obj_rating = [] #objective rating (higher/lower 5)
        scale_rating.reset() #subjective rating (seen/not seen)
#        scale_rating.setMarkerPos(random.randint(0,1))
        l = []
        real_soa = 0

        # moving dots
        outlet.push_sample(x=[0])

        fixation.setAutoDraw(False)

        for frameN in range(20): #20 times so the dots 'move' inwards
            dotUR.pos *= 0.87
            dotUL.pos *= 0.87
            dotDR.pos *= 0.87
            dotDL.pos *= 0.87
            dotUR.draw()
            dotUL.draw()
            dotDR.draw()
            dotDL.draw()
            win.callOnFlip(trial_clock.reset)
            win.flip()

        # start recording frame
        win.recordFrameIntervals = True
        win.resfreshThreshold = 1/60 + 0.002
        # assuming a refreshing rate of 60 Hz and 2 ms tolerance
        
        outlet.push_sample(x=[1])

        for frameN in range(ep_dur):
            # target presentation
            if 0 <= frameN < target_dur: #present target for the amount of frames of target_dur
                fixation.setAutoDraw(True)
                t.draw()
                win.flip()
                 #send target trigger!
#                win.callOnFlip(reset_clock_and_send_trigger,
#                              trial_list_df.loc[trial]['trigger'])
#                win.callOnFlip(reset_clock_and_send_trigger, 0)

            # SOA
            elif target_dur <= frameN < target_dur + soa_dur: #present blank screen after target for the amount of frames of soa_dur
                win.flip()

            # mask presentation & stop recording frame intervals
            elif target_dur + soa_dur <= frameN < target_dur + soa_dur + mask_dur:
                #mask trigger?
                mask_image.draw()

                win.flip()
                win.recordFrameIntervals = False

            else:
                mask_image.setAutoDraw(False)
                win.flip()

        # Objective response
        fixation.setAutoDraw(False)
        obj_order = visual.TextStim(
            win=win,
            text='Comparación con el número 5',
            color='black')
        obj_order.draw()
        win.callOnFlip(obj_clock.reset)
        win.flip()
        obj_rating = event.waitKeys(keyList=['left', 'right']) #change to other keys for other hand?
        obj_RT = obj_clock.getTime()
        subj = visual.TextStim(
            win=win,
            text='¿Viste el número?',
            pos=(0.0,0.3),
            color='black')
        # Subjective response
        while scale_rating.noResponse:
            scale_rating.draw()
            subj.draw()
            win.flip()

        SR = scale_rating.getRating()

        while SR == " ":
            scale_rating.reset()
            while scale_rating.noResponse:
                subj.draw()
                scale_rating.draw()
                win.flip()
            SR = scale_rating.getRating()

        if SR == "no visto":
            subj_rating = 0
        else:
            subj_rating = 1

        subj_RT = scale_rating.getRT()
        trial_dur = trial_clock.getTime()

        # Record frame interval
        l = win.frameIntervals[sumSOA:(sumSOA + soa_dur + target_dur)] 
        for j in l[1:]:
            real_soa = j + real_soa
        sumSOA = soa_dur + target_dur + sumSOA
        for frameN in range(20): #empty screen for 20 frames?
            win.flip()

        # fill the colums during the experiment
        col_participant.append(exp_info['Participant'])
        col_stim.append(exp_info['Stim'])
        col_session.append(exp_info['Session'])
        col_block.append(i+1)
        col_frame_rate.append(exp_info['frame_rate'])
        col_frame_int.append(l)
        col_real_soa.append(real_soa)
        col_order.append(trial)
        col_positions.append(trial_list_df.loc[trial]['position'])
        col_targets.append(trial_list_df.loc[trial]['target'])
        col_masks.append(trial_list_df.loc[trial]['mask'])
        col_soas.append(trial_list_df.loc[trial]['SOA'])
        col_answers.append(trial_list_df.loc[trial]['cor_ans'])
        col_obj_rating.append(obj_rating)
        col_obj_RT.append(obj_RT)
        col_subj_rating.append(subj_rating)
        col_subj_RT.append(subj_RT)
        col_trial_dur.append(trial_dur)
        col_trigger.append(trial_list_df.loc[trial]['trigger'])
    
    #change hands --> also change keys?
    if i == 1: #after the second block this message is shown
        textPause = visual.TextStim(
            win=win,
            text="A partir de este momento, utilizar la otra mano para responder \n"
            "Apretar la barra espaciadora o la tecla Enter para continuar",
            color='black')
        textPause.draw()
        win.flip()
        event.waitKeys(keyList=['space', 'num_enter'])
        for frameN in range(40):
            win.flip()

# Store the data in a dataframe
participant_df = pd.DataFrame({
    'subject': col_participant,
    'stim': col_stim,
    'session': col_session,
    'block': col_block,
    'frame_rate': col_frame_rate,
    'frame_int': col_frame_int,
    'trial_nb': col_order,
    'SOA': col_soas,
    'real_SOA': col_real_soa,
    'target': col_targets,
    'mask': col_masks,
    'position': col_positions,
    'cor_ans': col_answers,
    'obj_rating': col_obj_rating,
    'obj_RT': col_obj_RT,
    'subj_rating': col_subj_rating,
    'subj_RT': col_subj_RT,
    'trial_duration': col_trial_dur,
    'trigger': col_trigger})

print('Overall, %i frames were dropped' % win.nDroppedFrames)
# plt.plot(win.frameIntervals)

participant_df.to_excel(filename+'.xlsx')
participant_df.to_csv(filename+'.csv', sep=';')
win.saveFrameIntervals(filename+'_frame.csv')

# plt.show()
win.close()
core.quit()
