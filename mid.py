# Necessary imports
import os, random
import numpy as np
from psychopy import visual, core, event, gui
from psychopy.hardware import brainproducts
from PIL import Image

class MonetaryIncentiveDelayTask:
    """
    Those are the configurable attributes for learning and reverse conditions, EEG signaling, and visual stimuli timing.
    
    Trials:
        n_trials (int): Number of trials to conduct for each condition.
        seed_value (int): Seed for the random probability generator (fixed at -1 for replication purposes).
        learn_trial (dict): Positions of each box in the learning condition.
        reverse_trial (dict): Positions of each box in the reverse condition.    
                            
    EEG signaling:
        marker_duration (float): Duration of the EEG marker (red flash) in seconds.   
             
    Stimuli timing:
        fixation_time (float): Time for the fixation cross in seconds.
        soa_time (float): Stimulus onset asynchrony (variable for evoked potentials).
        result_time (float): Time for the result to be shown in seconds.
        iti_time (float): Inter-trial interval in seconds.
    """
        
    def __init__(self, subject_id, experiment_conedition, experiment_part):     
        # A value of -1 fixes seed for debug and replication purposes
        seed_value = 100
        if (seed_value > 0):            
            random.seed(seed_value)        
        
        # Number of trials for each condition:
        self.n_trials = 10
         
        if (experiment_part == 1):       
            # Define the reward for the test chests:        
            self.test_trial = [[0, 0, 0], [1, 1, 1]] # Fixed results. The first one is a -1, the second one a +1

            # Generate the positions for the learning and reverse conditions (learn and reverse trials must have their chests in different positions)
            learn_chest_positions, reverse_chest_positions = self.get_chest_positions(reward_percentage=[0.8, 0.5, 0.2]) # 80%, 50%, 20% of getting a reward (1)
            # Generate the refresh trials
            refresh_trials = self.generate_refresh_trials(10, learn_chest_positions)
            
            # Generate the whole trials for the learning and reverse learning chests.        
            self.learn_trial, self.reverse_trial = self.generate_trials(self.n_trials, learn_chest_positions, reverse_chest_positions)
        elif (experiment_part == 2):
            # Read the metadata from the previous part
            metadata = self.read_metadata()
            
            # Extract the chest positions and trials from the metadata
            learn_chest_positions = metadata[0]
            self.learn_trial = metadata[1]
            reverse_chest_positions = metadata[2]
            self.reverse_trial = metadata[3]            
                    
        # Define visual variables:
        self.win = visual.Window(fullscr=False, allowGUI=False, color='gainsboro', monitor='2', screen=1) # experimental window
        self.win_eeg_markers = visual.Window(size=(800, 600), color='black', units='pix') # eeg markers window        
        self.clock = core.Clock() # clock for timing the markers
        self.fixation_cross = visual.TextStim(self.win, text='+', color='black', height=0.2)
        
        # Define storage variables:
        self.trial_data = []
        self.results_file = f"results/{subject_id}_{experiment_condition}_part_{str(experiment_part)}.txt"
        self.experiment_condition = int(experiment_part)
        self.experiment_part = int(experiment_part)
        
        # Save general information about the experiment
        if (self.experiment_part == 1): 
            self.save_metadata([learn_chest_positions, self.learn_trial, reverse_chest_positions, self.reverse_trial])
            
    def eeg_connect(self):
        import time

        # Start the connection to RCS
        rcs = brainproducts.RemoteControlServer(host='127.0.0.1', port=6700, timeout=10.0, testMode=False) 
        rcs.openRecorder()
        time.sleep(1)
        rcs.mode = 'default' # Set the mode to default (aka idle state)
        time.sleep(1)      
        rcs.amplifier = 'LiveAmp', 'LA-05490-0200' #'Simulated Amplifier'
        rcs.open(expName = 'PsiloLearn', participant = subject_id, workspace = r'C:\Vision\Workfiles\PsiloLearn.rwksp')
        time.sleep(2)    
        return rcs

    def eeg_start_recording(self, rcs):
        import time             
        # Set the RCS to recording 
        rcs.mode = 'monitor'
        rcs.startRecording()
        time.sleep(2)
        
    def eeg_stop_recording(self, rcs):
        import time
        # End recording
        rcs.stopRecording()
        time.sleep(1)
        rcs.mode = 'default'  
        time.sleep(1)

    def eeg_pause_recording(self, rcs):
        import time
        # Pause recording
        rcs.pauseRecording()
        time.sleep(2)

    def eeg_resume_recording(self, rcs):
        import time
        # Resume recording
        rcs.resumeRecording()
        time.sleep(1)
        
    def eeg_send_marker(self, rcs, text, annot_type = 'ANNOT'):
        # Write annotation
        rcs.sendAnnotation(text, annot_type)          
            
    def get_chest_positions(self, reward_percentage):
        # Create a copy of the original probabilities
        learn_probability = reward_percentage.copy()    
        reverse_probability = reward_percentage.copy()
        # Now randomize the probabilities of the chests until all probabilities are different for each position
        sorted = False
        while not sorted:
            random.shuffle(learn_probability)
            random.shuffle(reverse_probability)
            if (learn_probability[0] != reverse_probability[0] and 
                learn_probability[1] != reverse_probability[1] and 
                learn_probability[2] != reverse_probability[2]):                
                sorted = True

        return learn_probability, reverse_probability
     
    def generate_trials(self, n_trials, learn_probability, reverse_probability):
        # Generate the trials for the learning and reverse conditions                      
        probability_array = [learn_probability, reverse_probability]
        result_array = []
        for i in range(2):              
            # First chest reward possibilities (amount of 1s and 0s in the array)
            chest1_ones = int(n_trials * probability_array[i][0])
            chest1_zeros = int(n_trials * round(1-probability_array[i][0], 1))
            # Second chest reward  possibilities (amount of 1s and 0s in the array)
            chest2_ones = int(n_trials * probability_array[i][1])
            chest2_zeros = int(n_trials * round(1-probability_array[i][1], 1))
            # Third chest reward  possibilities (amount of 1s and 0s in the array)
            chest3_ones = int(n_trials * probability_array[i][2])
            chest3_zeros = int(n_trials * round(1-probability_array[i][2], 1))
                    
            # Create the arrays for each chest
            # The first position accounts for the 1 and the second for the 0
            first_chest_array = [1] * chest1_ones + [0] * chest1_zeros
            second_chest_array = [1] * chest2_ones + [0] * chest2_zeros
            third_chest_array = [1] * chest3_ones + [0] * chest3_zeros
                            
            # Shuffle the arrays
            np.random.shuffle(first_chest_array)
            np.random.shuffle(second_chest_array)
            np.random.shuffle(third_chest_array)
            
            # Create the trial array, that includes the three chests
            trial_array = np.stack((first_chest_array, second_chest_array, third_chest_array), axis=1)
            result_array.append(trial_array)
                    
        # Return the two equally distributed conditions
        learn_trial = result_array[0]
        reverse_trial = result_array[1]
        return learn_trial, reverse_trial
    
    def generate_refresh_trials(self, n_trials, learn_chest_positions):
        position = learn_chest_positions.index(0.8)
        refresh_trial = [0] * 3
        refresh_trial[position] = 1
        result_array = []
        for i in range(n_trials):
            result_array.append(refresh_trial)   
        return result_array
    
    def show_text(self, text):
        instruction_text = text
        instructions = visual.TextStim(self.win, text=instruction_text, color='black', height=0.05, wrapWidth=1.7, alignText='left')
        instructions.draw()
        self.win.flip()
        event.waitKeys()

    def run_test_trials(self):
        # Test trials
        self.eeg_send_marker(self.rcs, 'test_trials_start') # EEG marker   
        for i in range(len(self.test_trial)):
            self.run_trial('test', i+1, self.test_trial[i])
        self.eeg_send_marker(self.rcs, 'test_trials_end') # EEG marker   
   
    def run_learning_trials(self):
        # Start the EEG recording        
        self.eeg_start_recording(self.rcs)
        try:
            self.eeg_send_marker(self.rcs, 'experiment_start') # EEG marker  
            
            # Learning trials
            self.eeg_send_marker(self.rcs, 'learning_trials_start') # EEG marker                     
            for i in range(self.n_trials):
                self.run_trial('learn', i+1, self.learn_trial[i]) # Pass the estimated reward of each trial as a parameter
            self.eeg_send_marker(self.rcs, 'learning_trials_end') # EEG marker            
            self.eeg_stop_recording(self.rcs)
            
            self.eeg_send_marker(self.rcs, 'experiment_end') # EEG marker  
            
        finally:
            # No matter what, this is allways executed:
            self.save_results()             
            self.eeg_stop_recording(self.rcs)   
   
    def run_refresh_learning_trials(self):
        pass  
   
    def run_reverse_learning_trials(self):
        # Start the EEG recording     
        self.eeg_start_recording(self.rcs)
        try:
            self.eeg_send_marker(self.rcs, 'experiment_start') # EEG marker
                      
            # Reverse learning trials
            self.eeg_send_marker(self.rcs, 'reverse_learning_trials_start') # EEG marker
            for i in range(self.n_trials):
                self.run_trial('reverse', i+1, self.reverse_trial[i]) # Pass the estimated reward of each trial as a parameter            
            self.eeg_send_marker(self.rcs, 'reverse_learning_trials_end') # EEG marker  
        finally:
            # No matter what, this is allways executed:
            self.save_results()             
            self.eeg_stop_recording(self.rcs)
            self.eeg_send_marker(self.rcs, 'experiment_end') # EEG marker    
          
    win call on flip
          
    def run(self):
        # Connect EEG
        self.rcs = self.eeg_connect()              
         
        if (self.experiment_part == 1):
            self.show_text('¡Bienvenidx! Por favor leé con atención.\n\n\n\n'
                            'La tarea que estás por realizar consta de varios ensayos como el siguiente:\n\n'
                            '   * Aparecerán tres cofres en pantalla. Cada uno tiene una probabilidad de recompensa diferente.\n\n'
                            '   * Elegí uno presionando alguna de las teclas: izquierda, abajo o derecha.\n\n'              
                            '   * Te preguntaremos cuán seguro estás de que tu elección es correcta.\n\n'                                 
                            '   * Finalmente te mostraremos el resultado (+1, -1).\n\n'                                               
                            '   * ¡El objetivo de la tarea es obtener la mayor cantidad de monedas posibles!\n\n\n\n'                      
                            'Presiona cualquier tecla para comenzar una ronda de prueba.')              
            
            # Test trials
            self.run_test_trials() 

            self.show_text('¡Lo hiciste perfecto! Unas últimas aclaraciones:\n\n\n\n'
                            '   * Luego de la elección del cofre, mantené la vista en la cruz de fijación.\n\n'
                            '   * Se registrará la señal de EEG durante todo el experimento, por lo cual evitá moverte.\n\n'
                            '   * Evitá pestañear, a no ser que te encuentres en la pantalla de los cofres.".\n\n'
                            '   * Si tenés alguna duda podés preguntarnos ahora ya que durante la tarea no habrá interacción con los investigadores.\n\n\n\n'                        
                            'Ahora si, cuando estés listx presiona cualquier tecla para comenzar :)')                  
            
            # Learning trials
            self.run_learning_trials()
        
            self.show_text('¡Listo por ahora! \n\n'
                        'Por favor contactate con el investigador a cargo.')                 
        
        elif (self.experiment_part == 2):
                        
            # Refresh learning trials
            self.run_refresh_learning_trials()
            
            # Reverse learning trials:
            self.run_reverse_learning_trials()

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
        
        self.eeg_send_marker(self.rcs, 'trial_start') # EEG marker
        
        ## STIMULI BLOCK
        # Create the fixation cross (pre stimuli)
        self.fixation_cross.draw()
        self.win.flip()
        self.eeg_send_marker(self.rcs, 'stimuli_fixation_shown') # EEG marker
        core.wait(fixation_time) 
        
        # Create and show the chests
        self.draw_chests()
        self.win.flip()
        start_time = core.getTime()
        while True:
            keys = event.waitKeys(keyList=['left', 'down', 'right', 'escape'])
            if keys[0] == 'escape':
                self.eeg_send_marker(self.rcs, 'experiment_halted') # EEG marker
                core.quit()            
            elif keys[0] in ['left', 'down', 'right']:
                selected_chest = ['left', 'down', 'right'].index(keys[0]) # returns 0, 1, 2
                chest_latency = int((core.getTime() - start_time) * 1000)
                self.eeg_send_marker(self.rcs, 'key_pressed_chest') # EEG marker
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
        self.eeg_send_marker(self.rcs, 'result_fixation_shown') # EEG marker
        core.wait(soa_time) 

        # Show feedback
        color = 'red'
        if result_text == '+1':
            color = 'green'
        feedback = visual.TextStim(self.win, text=result_text, color=color, height=0.15, bold=True)
        feedback.draw()
        self.win.flip()
        self.eeg_send_marker(self.rcs, 'feedback_shown') # EEG marker
        core.wait(result_time)

        # Ask for the confidence level
        self.draw_confidence_scale()
        self.win.flip()  
        start_time = core.getTime()
        current_selection = -1
        on_selection = True
        while on_selection:
            core.wait(0.1)
            keys = event.waitKeys(keyList=['left', 'right', 'up', 'escape'])
            if keys[0] == 'escape':                
                self.eeg_send_marker(self.rcs, 'experiment_halted') # EEG marker
                core.quit()            
            elif keys[0] in ['left', 'right']:
                selected_direction = ['left', 'right'].index(keys[0]) # returns 0, 1                   
                # Draw the frame around the selected option
                if (current_selection == -1):
                    # First time drawing the frame, must choose between center right and left
                    current_selection = 1 if selected_direction == 0 else 2                        
                else:    
                    # If the current selection is not the first or last, move the frame            
                    if (selected_direction == 0) and (current_selection != 0):
                        current_selection = current_selection - 1
                    elif (selected_direction == 1) and (current_selection != 3):
                        current_selection = current_selection + 1                                  
                # Draw the confidence scale with the new selection             
                self.draw_confidence_scale(current_selection)
                self.win.flip()                
            elif keys[0] in ['up']:
                selected_confidence = current_selection
                confidence_latency = int((core.getTime() - start_time) * 1000)                
                self.eeg_send_marker(self.rcs, 'key_confidence_selected') # EEG marker
                # Break the loop
                on_selection = False       
 
        # Accumulate the result
        result = calc_result(self, hit)
        streak = self.trial_data[-1][7] + 1 if len(self.trial_data) > 0 and bool(hit) else hit 
        self.trial_data.append([cond, trial_n, trial_reward, chest_latency, selected_chest, confidence_latency, selected_confidence, hit, result, streak])
                       
        self.eeg_send_marker(self.rcs, 'trial_end') # EEG marker
        
        ## ITI BLOCK
        # Clear the screen 
        core.wait(iti_time)
        """
        if (trial_n in [20, 40]):
            self.show_text('Presione una tecla para continuar.') 
        """
        
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

    def draw_confidence_scale(self, current_selection = -1):
       # Define confidence levels and corresponding colors
        levels = ['Completa', 'Bastante', 'Poco', 'Nada']
        # colors = {levels[0]: 'limegreen', levels[1]: 'olivedrab', levels[2]: 'olive', levels[3]: 'tomato'}
        # Create TextStim for the instruction
        instruction_text = '¿Cuánta confianza tenías en tu elección?'	
        instructions = visual.TextStim(self.win, text=instruction_text, color='black', height=0.08, wrapWidth=1.7)
        instructions.pos = (0, 0.4)        
        # Shuffle the order of confidence levels
        # random.shuffle(levels)         
        confidence_stims = []
        initial_x = -0.4 * (len(levels) - 1) / 2 # Center the scale
        for i, level in enumerate(levels):
            # If redrawing, check if the current level is selected
            if i > -1:
                selected = True if i == current_selection else False        

            confidence_stim = visual.TextStim(self.win, text=level, color='black', height=0.1, bold=selected)        
            confidence_stim.pos = (initial_x + i * 0.4, 0)
            confidence_stims.append(confidence_stim)
        # Draw the instruction and confidence levels
        instructions.draw()            
        for stim in confidence_stims:
            stim.draw()

    def save_metadata(self, data):
        # Create the folder if it doesn't exist
        results_dir = os.path.dirname(self.results_file)
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        # Save the results:
        with open(self.results_file, 'a') as f:
            learn_list = [list(sublista) for sublista in data[1]] 
            reverse_list = [list(sublista) for sublista in data[3]] 
            f.write("learn_reward;learn_trials;reverse_reward;reverse_trials\n")
            f.write(f"{data[0]};{learn_list};{data[2]};{reverse_list};\n")

    def read_metadata(self):
        # Check if the file exists
        if not os.path.exists(self.results_file):
            return None

        # Open the file for reading
        with open(self.results_file, 'r') as f:
            # Skip the header line
            next(f)

            # Read the data line
            data_line = f.readline()

            # Check if the line is empty or contains only newline character
            if not data_line.strip():
                return None

            # Split the data line by semicolon and convert to float
            data = [float(value) for value in data_line.split(';')]

            # Return a list containing the four saved values
            return data[0:4]


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
    dlg.addText("Por favor, ingresa ID, condición y parte del sujeto:")
    dlg.addField("Sujeto: ", "s")
    dlg.addField('Condición:', choices=["A", "B"])
    dlg.addField('Parte:', choices=["1", "2"])
    data = dlg.show()
    if dlg.OK:
        subject_id = data[0]
        experiment_condition = data[1]
        experiment_part = int(data[2])
        task = MonetaryIncentiveDelayTask(subject_id, experiment_condition, experiment_part)
        task.run()