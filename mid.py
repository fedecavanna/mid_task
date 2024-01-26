# Necessary imports
import os
import random
from psychopy import visual, core, event, gui
from pylsl import StreamInfo, StreamOutlet
from PIL import Image

class MonetaryIncentiveDelayTask:

    """
    Those are the configurable attributes for learning and reverse conditions, EEG signaling, and visual stimuli timing.
    
    Trials:
        n_trials (int): Number of trials to conduct for each condition.
        seed_value (int): Seed for the random probability generator (fixed at -1 for replication purposes).
        learn_trial (dict): Probabilities of each box in the learning condition.
        reverse_trial (dict): Probabilities of each box in the reverse condition.    
                            
    EEG signaling:
        marker_duration (float): Duration of the EEG marker (red flash) in seconds.   
             
    Stimuli timing:
        fixation_time (float): Time for the fixation cross in seconds.
        soa_time (float): Stimulus onset asynchrony (variable for evoked potentials).
        result_time (float): Time for the result to be shown in seconds.
        iti_time (float): Inter-trial interval in seconds.
    """
        
    def __init__(self, subject_id):     
        # Create an LSL stream for sending markers
        self.info = StreamInfo(name='MarkerStream', type='Markers', channel_count=1, channel_format='string', source_id='myuidw43536')
        self.outlet = StreamOutlet(self.info)
        
        # Number of trials for each condition:
        self.n_trials = 2
        
        # Define the reward for the chests:
        # Each number in the probability set eg [0.8, 0.2] is the chance for each option [0, 1].
        self.test_trial = [[0, 0, 0], [1, 1, 1]] # Fixed results. The first one is a -1, the second one a +1
        self.learn_trial = self.populate_trial_data(self.n_trials, [[0.8, 0.2], [0.5, 0.5], [0.2, 0.8]]) # right box > left box
        self.reverse_trial = self.populate_trial_data(self.n_trials, [[0.2, 0.8], [0.5, 0.5], [0.8, 0.2]]) # left box > right box       
        
        # Define visual variables:
        self.win = visual.Window(fullscr=True, allowGUI=False, color='gainsboro', monitor='2', screen=1) # experimental window
        self.win_eeg_markers = visual.Window(size=(800, 600), color='black', units='pix') # eeg markers window        
        self.clock = core.Clock() # clock for timing the markers
        self.fixation_cross = visual.TextStim(self.win, text='+', color='black', height=0.2)
        
        # Define storage variables:
        self.trial_data = []
        self.results_file = f"results/{subject_id}.txt"
            
    def send_eeg_marker(self):        
        colors = ['red', 'black']
        # 60 Hz monitor = 1/60 = 0.0167 seconds per frame
        marker_duration = 0.0167 * 4 # Flash for n frames

        # Flash red for 'duration'
        while self.clock.getTime() < marker_duration:
            for color in colors:
                self.win_eeg_markers.color = color
                self.win_eeg_markers.flip()
                
                # I'll exit the loop once duration is reached
                if self.clock.getTime() >= marker_duration:
                    break

        # Then go back to black again.
        self.win_eeg_markers.color = 'black'
        self.win_eeg_markers.flip()


    def populate_trial_data(self, n_trials, proba):
        # Fixed seed for replication purposes
        seed_value = -1 
        if (seed_value > 0):            
            random.seed(seed_value)
        
        # Define the occurrence of each box based on the given probabilities
        options = [0, 1]
        box_1 = random.choices(options, proba[0], k=n_trials)
        box_2 = random.choices(options, proba[1], k=n_trials)
        box_3 = random.choices(options, proba[2], k=n_trials)
        
        # Create the trial data based on the previously calculated array
        result = []
        for i in range(self.n_trials):
            result.append([box_1[i], box_2[i], box_3[i]])
        print(result)
        return result

    def show_text(self, text):
        instruction_text = text
        instructions = visual.TextStim(self.win, text=instruction_text, color='black', height=0.05, wrapWidth=1.7, alignText='left')
        instructions.draw()
        self.win.flip()
        event.waitKeys()

    def run(self):
        self.outlet.push_sample(['experiment_start']) # EEG marker
        self.show_text('¡Bienvenidx! Por favor leé con atención.\n\n\n\n'
                        'La tarea que estás por realizar consta de varios ensayos como el siguiente:\n\n'
                        '   * Aparecerán tres cofres en pantalla. Cada uno tiene una probabilidad de recompensa diferente.\n\n'
                        '   * Elegí uno presionando alguna de las teclas: izquierda, abajo o derecha.\n\n'              
                        '   * Te preguntaremos cuán seguro estás de que tu elección es correcta.\n\n'                                 
                        '   * Finalmente te mostraremos el resultado (+1, -1).\n\n'                                               
                        '   * ¡El objetivo de la tarea es obtener la mayor cantidad de monedas posibles!\n\n\n\n'                      
                        'Presiona cualquier tecla para comenzar una ronda de prueba.')

        for i in range(len(self.test_trial)):
            self.run_trial('test', i+1, self.test_trial[i])
        
        self.show_text('¡Lo hiciste perfecto! Unas últimas aclaraciones:\n\n\n\n'
                        '   * Luego de la elección del cofre, mantené la vista en la cruz de fijación.\n\n'
                        '   * Se registrará la señal de EEG durante todo el experimento, por lo cual evitá moverte y en lo posible evitá pestañear.\n\n'
                        '   * Para que tomes un respiro, cada cierta cantidad de ensayos aparecerá un cartel diciendo "Presione una tecla para continuar".\n\n'
                        '   * Si tenés alguna duda podés preguntarnos ahora ya que durante la tarea no habrá interacción con los investigadores.\n\n\n\n'                        
                        'Ahora si, cuando estés listx presiona cualquier tecla para comenzar :)')        
                
        for i in range(self.n_trials):
            self.run_trial('learn', i+1, self.learn_trial[i]) # Pass the estimated reward of each trial as a parameter
        for i in range(self.n_trials):
            self.run_trial('reverse', i+1, self.reverse_trial[i]) # Pass the estimated reward of each trial as a parameter
            
        self.outlet.push_sample(['experiment_end']) # EEG marker
        self.save_results() 
        
        self.show_text('¡Lo hiciste perfecto! Muchas gracias por participar :)\n\n\n\n'                      
                        'Presiona cualquier tecla para finalizar.')
        
    def run_trial(self, cond, trial_n, trial_reward):
        # Each trial is performed as follows
        # [fixation_stimuli + stimuli] [gap] [fixation_result + result] [confidence] [iti]
        
        fixation_time = 1.5 # Time for the fixation cross. 
        soa_time = random.uniform(1, 4) # Time before the result is shown
        result_time = 1 # Time for the result to be shown
        iti_time = 0.5 # Interval between trials
        
        # Handle the counter for the total gain-loss result:
        def calc_result(self, hit): 
            # Get the last count
            n = self.trial_data[-1][6] if len(self.trial_data) > 0 else 0
            # Evaluate whether to add or subtract and return
            res = n+1 if hit == 1 else n-1 
            return res
        
        self.outlet.push_sample(['trial_start']) # EEG marker
        
        ## STIMULI BLOCK
        # Create the fixation cross (pre stimuli)
        self.fixation_cross.draw()
        self.win.flip()
        self.outlet.push_sample(['stimuli_fixation_shown']) # EEG marker
        core.wait(fixation_time) 
        
        # Create and show the chests
        self.draw_chests()
        self.win.flip()
        start_time = core.getTime()
        while True:
            keys = event.waitKeys(keyList=['left', 'down', 'right', 'escape'])
            if keys[0] == 'escape':
                self.outlet.push_sample(['experiment_halted']) # EEG marker
                core.quit()            
            elif keys[0] in ['left', 'down', 'right']:
                selected_chest = ['left', 'down', 'right'].index(keys[0]) # returns 0, 1, 2
                chest_latency = int((core.getTime() - start_time) * 1000)
                self.outlet.push_sample(['key_pressed_chest']) # EEG marker
                break            
             
        ## GAP BLOCK
        # Clear the screen 
        self.win.flip()

        # Check if they hit the box               
        hit = trial_reward[selected_chest]
        result_text = '+1' if hit else '-1'

        ## RESULTS BLOCK
        # Create the fixation cross (pre results)
        self.fixation_cross.draw()
        self.win.flip()
        self.outlet.push_sample(['result_fixation_shown']) # EEG marker
        core.wait(soa_time) 

        # Show feedback
        color = 'red'
        if result_text == '+1':
            color = 'green'
        feedback = visual.TextStim(self.win, text=result_text, color=color, height=0.15, bold=True)
        feedback.draw()
        self.win.flip()
        self.outlet.push_sample(['feedback_shown']) # EEG marker
        core.wait(result_time)

        # Ask for the confidence level
        self.draw_confidence_scale()
        self.win.flip()             
        start_time = core.getTime()
        while True:
            keys = event.waitKeys(keyList=['left', 'down', 'right', 'escape'])
            if keys[0] == 'escape':
                self.outlet.push_sample(['experiment_halted']) # EEG marker
                core.quit()            
            elif keys[0] in ['left', 'down', 'right']:
                selected_confidence = ['left', 'down', 'right'].index(keys[0]) # returns 0, 1, 2
                confidence_latency = int((core.getTime() - start_time) * 1000)
                self.outlet.push_sample(['key_pressed_confidence']) # EEG marker
                break

        # Accumulate the result
        result = calc_result(self, hit)
        streak = self.trial_data[-1][7] + 1 if len(self.trial_data) > 0 and bool(hit) else hit 
        self.trial_data.append([cond, trial_n, trial_reward, chest_latency, selected_chest, confidence_latency, selected_confidence, hit, result, streak])
        trial_data_str = ', '.join(f"{cond};{trial_n};{trial_reward};{chest_latency};{selected_chest};{hit};{result};{streak}")
                       
        self.outlet.push_sample([trial_data_str]) # EEG marker 
        self.outlet.push_sample(['trial_end']) # EEG marker 
        
        ## ITI BLOCK
        # Clear the screen 
        core.wait(iti_time)
        if (trial_n in [20, 40]):
            self.show_text('Presione una tecla para continuar.') 
    
    def draw_chests(self):
        # Create the chest images
        chests = []
        for i in range(3):
            image = Image.open('assets/chest_2.png')
            chest = visual.ImageStim(self.win, image=image, size=0.3)
            chest.pos = ((i - 1) * 0.6, 0)
            chests.append(chest)
        for chest in chests:
            chest.draw()

    def draw_confidence_scale(self):
       # Define confidence levels and corresponding colors
        levels = ['Mucho', 'Algo', 'Nada']
        colors = {levels[0]: 'limegreen', levels[1]: 'olive', levels[2]: 'tomato'}            
        # Create TextStim for the instruction
        instruction_text = '¿Cuán seguro estabas de ganar una moneda?'	
        instructions = visual.TextStim(self.win, text=instruction_text, color='black', height=0.08, wrapWidth=1.7)
        instructions.pos = (0, 0.4)        
        # Shuffle the order of confidence levels
        random.shuffle(levels)         
        confidence_stims = []
        for i, level in enumerate(levels):
            confidence_stim = visual.TextStim(self.win, text=level, color=colors[level], height=0.1)
            confidence_stim.pos = ((i - 1) * 0.6, 0)
            confidence_stims.append(confidence_stim)
        # Draw the instruction and confidence levels
        instructions.draw()            
        for stim in confidence_stims:
            stim.draw()

    def save_results(self):
        # Create the folder if it doesn't exist
        results_dir = os.path.dirname(self.results_file)
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        # Save the results:
        with open(self.results_file, 'a') as f:
            f.write("cond;trial_n;trial_setup;chest_latency_ms;chest_sel;confidence_latency_ms;confidence_sel;hit;result;streak\n")
            for i, data in enumerate(self.trial_data):
                f.write(f"{data[0]};{data[1]};{data[2]};{data[3]};{data[4]};{data[5]};{data[6]};{data[7]}\n")

if __name__ == "__main__": 
    # Request any relevant information needed:
    dlg = gui.Dlg(title="Información")
    dlg.addText("Por favor, ingresa el ID del sujeto:")
    dlg.addField("Sujeto: ", "s")
    subject_id = dlg.show()
    if dlg.OK:
        task = MonetaryIncentiveDelayTask(subject_id[0])
        task.run()
