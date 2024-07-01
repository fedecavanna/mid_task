# Necessary imports
import os, random, time
import numpy as np
from psychopy import visual, core, event, gui
from psychopy.hardware import brainproducts
from PIL import Image

class EEGInterface:     
    debug = False   
    def eeg_connect(self, subject_id, experiment_condition, experiment_part):
        if not self.debug:
            # Start the connection to RCS        
            self.rcs = brainproducts.RemoteControlServer(host='127.0.0.1', port=6700, timeout=10.0, testMode=False) 
            self.rcs.openRecorder()
            core.wait(1)
            self.rcs.mode = 'default' # Set the mode to default (aka idle state)
            core.wait(1)      
            # self.rcs.amplifier = 'Simulated Amplifier', 'LA-05490-0200'
            self.rcs.amplifier = 'BrainAmp Family'
            subject_tag = f"{subject_id}_{experiment_condition}_part_{str(experiment_part)}"
            self.rcs.open(expName = 'PsiloLearn', participant = subject_tag, workspace = r'C:\Vision\Workfiles\PsiloLearn.rwksp')
            core.wait(2)    
        
    def eeg_start_recording(self):   
        if not self.debug:     
            # Set the RCS to recording 
            self.rcs.mode = 'monitor'    
            self.rcs.startRecording()
            core.wait(2)
     
    def eeg_stop_recording(self):
        if not self.debug:
            # End recording
            self.rcs.stopRecording()
            self.rcs.mode = 'default'  
            core.wait(1)
    
    def eeg_pause_recording(self):
        if not self.debug:
            # Pause recording
            self.rcs.pauseRecording()
            core.wait(2)
    
    def eeg_resume_recording(self):
        if not self.debug:
            # Resume recording
            self.rcs.resumeRecording()
            core.wait(1)

    def eeg_send_marker(self, text, annot_type = 'ANNOT'):
        if not self.debug:
            # Write annotation
            if self.rcs.mode != 'monitor':
                self.rcs.mode = 'monitor'                
            self.rcs.sendAnnotation(text, annot_type)            

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
            
    def __init__(self, subject_id, experiment_condition, experiment_part):     
        # A value of -1 fixes seed for debug and replication purposes        
        seed_value = int(time.time())
        if (seed_value > 0):            
            random.seed(seed_value)        
        
        # Init the interface to the EEG
        self.eeg_interface = EEGInterface()
        
        # Define experiment variables:
        self.trial_data = []
        self.metadata_file = f"results/{subject_id}/{subject_id}_metadata_part_{(experiment_condition)}.txt"
        self.results_file = f"results/{subject_id}/{subject_id}_{experiment_condition}_part_{str(experiment_part)}.txt"
        self.subject_id = subject_id
        self.experiment_condition = experiment_condition
        self.experiment_part = int(experiment_part)        
        
        # Number of trials for each condition:
        self.n_trials = 80
        refresh_n_trials = 10
         
        if (experiment_part == 1):       
            # Define the reward for the test chests:        
            self.test_trial = [[0, 0, 0], [1, 1, 1]] # Fixed results. The first one is a -1, the second one a +1

            # Generate the positions for the learning and reverse conditions (learn and reverse trials must have their chests in different positions)
            learn_chest_positions, reverse_chest_positions = self.get_chest_positions(reward_percentage=[0.8, 0.5, 0.2]) # 80%, 50%, 20% of getting a reward (1)
            # Generate the refresh trials
            refresh_trials = self.generate_refresh_trials(refresh_n_trials, learn_chest_positions)
            
            # Generate the whole trials for the learning and reverse learning chests.        
            self.learn_trial, self.reverse_trial = self.generate_trials(self.n_trials, learn_chest_positions, reverse_chest_positions)
        elif (experiment_part == 2):
            # Read the metadata from the previous part
            metadata = self.read_metadata()
            
            # Extract the chest positions and trials from the metadata
            learn_chest_positions = metadata[0]
            self.learn_trial = metadata[1]
            self.refresh_trials = metadata[2]
            reverse_chest_positions = metadata[3]
            self.reverse_trial = metadata[4]            
                    
        # Define visual variables:
        self.win = visual.Window(fullscr=True, allowGUI=False, color='gainsboro', monitor='2', screen=1) # experimental window
        self.win_eeg_markers = visual.Window(size=(800, 600), color='black', units='pix') # eeg markers window        
        self.clock = core.Clock() # clock for timing the markers
        self.fixation_cross = visual.TextStim(self.win, text='+', color='black', height=0.2)
        
        # Save general information about the experiment
        if (self.experiment_part == 1): 
            self.save_metadata([learn_chest_positions, self.learn_trial, refresh_trials, reverse_chest_positions, self.reverse_trial])
                 
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
    
    def show_text(self, text, timeout=0):
        instruction_text = text
        instructions = visual.TextStim(self.win, text=instruction_text, color='black', height=0.07, wrapWidth=1.7, alignText='left')
        instructions.draw()
        self.win.flip()
        if timeout > 0:
            core.wait(timeout)
        event.waitKeys()

    def run_test_trials(self):
        # Test trials
        self.eeg_interface.eeg_send_marker('test_trials_start') # EEG marker   
        for i in range(len(self.test_trial)):
            self.run_trial('test', i+1, self.test_trial[i])
            
    def run_learning_trials(self):
        # Start the EEG recording        
        self.eeg_interface.eeg_start_recording()
        try:
            self.eeg_interface.eeg_send_marker('experiment_start') # EEG marker  
            
            # Learning trials
            self.eeg_interface.eeg_send_marker('learning_trials_start') # EEG marker                     
            for i in range(self.n_trials):
                self.run_trial('learn', i+1, self.learn_trial[i]) # Pass the estimated reward of each trial as a parameter
            self.eeg_interface.eeg_send_marker('learning_trials_end') # EEG marker                        
        finally:
            # No matter what, this is allways executed:
            self.save_results()             
            self.eeg_interface.eeg_send_marker('experiment_end') # EEG marker  
            self.eeg_interface.eeg_stop_recording()   
   
    def run_reverse_learning_trials(self):
        # Start the EEG recording     
        self.eeg_interface.eeg_start_recording()
        try:
            self.eeg_interface.eeg_send_marker('experiment_start') # EEG marker
              
            # Refresh learning
            self.eeg_interface.eeg_send_marker('refresh_learning_trials_start') # EEG marker
            for i in range(len(self.refresh_trials)):
                self.run_trial('refresh', i+1, self.refresh_trials[i]) # Pass the estimated reward of each trial as a parameter            
            self.eeg_interface.eeg_send_marker('refresh_learning_trials_end') # EEG marker                    
                      
            # Reverse learning trials
            self.eeg_interface.eeg_send_marker('reverse_learning_trials_start') # EEG marker
            for i in range(self.n_trials):
                self.run_trial('reverse', i+1, self.reverse_trial[i]) # Pass the estimated reward of each trial as a parameter            
            self.eeg_interface.eeg_send_marker('reverse_learning_trials_end') # EEG marker  
        finally:
            # No matter what, this is allways executed:
            self.save_results()             
            self.eeg_interface.eeg_send_marker('experiment_end') # EEG marker
            self.eeg_interface.eeg_stop_recording()            
                    
    def run(self):
        # Connect EEG    
        self.show_text('Presioná una tecla para conectar el EEG...', 0)            
        self.eeg_interface.eeg_connect(self.subject_id, self.experiment_condition, self.experiment_part)              
         
        if (self.experiment_part == 1):
            self.show_text('¡Bienvenidx!\n\n'
                        'El objetivo del juego es descubrir cuál de los tres cofres es el Cofre Pirata.\n\n'
                        'En cada ensayo:\n'
                        ' - Aparecerán tres cofres en pantalla\n'
                        ' - Cada cofre contiene fichas que pueden darte dinero o quitártelo\n'
                        ' - Los cofres tienen diferentes probabilidades de hacerte ganar o perder\n'
                        ' - Por ejemplo, un cofre puede tener en su interior 40% de fichas ganadoras y 60% de fichas perdedoras.\n'
                        ' - La posición de los cofres es estable, aunque puede llegar a cambiar una vez durante el juego (no necesariamente)\n\n'                        
                        'Deberás seguir estos pasos:\n'
                        ' 1. Elegir un cofre presionando la tecla correspondiente\n'
                        ' 2. Indicar cuán seguro estás de que ese cofre te dará plata\n'
                        ' 3. Se te mostrará el resultado: +$10 o -$10\n\n'
                        'Recordá que tu objetivo es descubrir el cofre con mayor probabilidad de ganar, para llevarte la mayor cantidad de dinero.\n\n'
                        'Presiona cualquier tecla para comenzar una ronda de prueba.')    
            
            # Test trials
            self.run_test_trials() 

            self.show_text('¡Lo hiciste perfecto! Unas últimas aclaraciones:\n\n\n\n'
                            ' - Luego de la elección del cofre, mantené la vista fija en la cruz hasta ver el resultado.\n\n'
                            ' - Se registrará la señal de EEG durante todo el experimento, por lo cual evitá moverte.\n\n'
                            ' - Evitá pestañear, a no ser que te encuentres en la pantalla de los cofres.\n\n'
                            ' - Si tenés alguna duda podés preguntarnos ahora ya que durante la tarea no habrá interacción con los investigadores.\n\n\n\n'                        
                            'Ahora si, cuando estés listx presiona cualquier tecla para comenzar :)')                  
            
            # Learning trials
            self.run_learning_trials()
        
            self.show_text('¡Listo por ahora! \n\n'
                        'Por favor contactate con el investigador a cargo.', 10)                 
        
        elif (self.experiment_part == 2):        
            self.show_text('Bienvenidx nuevamente.\n\n\n\n'
                           'Vamos a continuar el juego en el punto lo dejaste.\n\n'
                           'Por favor, recordá:\n\n'
                            ' - Luego de la elección, mantené la vista fija en la cruz hasta ver el resultado.\n\n'
                            ' - Evitá moverte ya que afecta la señal que estamos midiendo.\n\n'
                            ' - Evitá pestañear, a no ser que te encuentres en la pantalla de los cofres.\n\n'
                            ' - Si tenés alguna duda podés preguntarnos ahora ya que durante la tarea no habrá interacción con los investigadores.\n\n\n\n'
                            'Nuevamente, cuando estés listx presiona cualquier tecla para comenzar :)')              
                                           
            # Refresh trials + Reverse learning trials:
            self.run_reverse_learning_trials()

            self.show_text('¡Lo hiciste perfecto! Muchas gracias por participar :)\n\n\n\n'                      
                            'Presiona cualquier tecla para finalizar.')
        
    def run_trial(self, cond, trial_n, trial_reward):
        # Each trial is performed as follows
        # [fixation_stimuli + stimuli] [confidence] [fixation_result + result] [iti]
        
        fixation_time = 1.5 # Time for the fixation cross. 
        soa_time = random.uniform(1, 4) # Time before the result is shown
        result_time = 1 # Time for the result to be shown
        iti_time = 0.5 # Interval between trials
        
        # Handle the counter for the total gain-loss result:
        def calc_result(self, hit): 
            # Get the last count
            n = int(self.trial_data[-1][8]) if len(self.trial_data) > 0 else 0
            # Evaluate whether to add or subtract and return
            res = n+10 if hit == 1 else n-10 
            return res
                        
        self.eeg_interface.eeg_send_marker('trial_start') # EEG marker
                
        """
        # Fixation cross red test
        self.red_background = visual.Rect(self.win, width=self.win.size[0], height=self.win.size[1], fillColor='red', lineColor=None)
        self.red_background.draw()                
        """
        self.fixation_cross.draw()        
        self.win.callOnFlip(self.eeg_interface.eeg_send_marker, 'stimuli_fixation_shown') # EEG marker   
        self.win.flip() 
        core.wait(fixation_time) 
        
        # Create and show the chests
        self.draw_chests()
        self.win.flip()
        start_time = core.getTime()
        keys = event.waitKeys(keyList=['left', 'down', 'right', 'escape'])
        if keys[0] == 'escape':                
            self.eeg_interface.eeg_send_marker('experiment_halted') # EEG marker
            core.quit()            
        elif keys[0] in ['left', 'down', 'right']:
            selected_chest = ['left', 'down', 'right'].index(keys[0]) # returns 0, 1, 2
            chest_latency = int((core.getTime() - start_time) * 1000)                
            self.eeg_interface.eeg_send_marker('key_pressed_chest') # EEG marker         
        
        # Ask for the confidence level
        self.draw_confidence_scale()
        self.win.flip()  
        start_time = core.getTime()
        keys = event.waitKeys(keyList=['1', '2', '3', '4', 'escape'])
        if keys[0] == 'escape':                                
            self.eeg_interface.eeg_send_marker('experiment_halted') # EEG marker
            core.quit()    
        elif keys[0] in ['1', '2', '3', '4']:       
                selected_confidence = keys[0]
                confidence_latency = int((core.getTime() - start_time) * 1000)                                    
                self.eeg_interface.eeg_send_marker('key_confidence_selected') # EEG marker

        ## RESULTS BLOCK
        # Check if they hit the box               
        hit = trial_reward[selected_chest]
        result_text = '+$10' if hit else '-$10'        
        
        # Create the fixation cross (pre results)
        self.fixation_cross.draw()        
        self.win.callOnFlip(self.eeg_interface.eeg_send_marker, 'result_fixation_shown') # EEG marker
        self.win.flip()
        
        # Variable SOA
        core.wait(soa_time) 

        # Show feedback
        color = 'red'
        background_color = '#ffdbdb'
        if result_text == '+$10':
            color = 'green'
            background_color = '#d3ffd9'
        self.result_background = visual.Rect(self.win, width=self.win.size[0], height=self.win.size[1], fillColor=background_color, lineColor=None)        
        self.result_background.draw()                    
        feedback = visual.TextStim(self.win, text=result_text, color=color, height=0.15, bold=True)        
        feedback.draw()                
        self.win.callOnFlip(self.eeg_interface.eeg_send_marker, 'feedback_shown') # EEG marker
        self.win.flip()
        core.wait(result_time)

        # Accumulate the result 
        result = calc_result(self, hit)
        streak = self.trial_data[-1][7] + 1 if len(self.trial_data) > 0 and bool(hit) else hit 
        self.trial_data.append([cond, trial_n, trial_reward, chest_latency, selected_chest, confidence_latency, selected_confidence, hit, result, streak])
                
        self.eeg_interface.eeg_send_marker('trial_end') # EEG marker1
        
        ## ITI BLOCK
        # Clear the screen 
        core.wait(iti_time)

    def draw_chests(self):
        # Create the chest images
        chests = []
        for i in range(3):
            image = Image.open('assets/chest_2.png')
            chest = visual.ImageStim(self.win, image=image, size=0.3)
            chest.pos = ((i - 1) * 0.6, 0)
            chests.append(chest)
            
        # Create the arrow images
        arrows = []
        arrow_left = visual.ImageStim(self.win, image='assets/key_left.png')
        arrow_left.pos = (-0.6, -0.3)
        arrows.append(arrow_left)

        arrow_down = visual.ImageStim(self.win, image='assets/key_down.png')
        arrow_down.pos = (0, -0.3)
        arrows.append(arrow_down)

        arrow_right = visual.ImageStim(self.win, image='assets/key_right.png')
        arrow_right.pos = (0.6, -0.3)
        arrows.append(arrow_right)

        # Draw the chests
        for i, chest in enumerate(chests):
            chest.draw()
            # Draw the accumulated result over the middle chest
            if i == 1:
                result = '$0'
                if self.trial_data and len(self.trial_data) > 0:
                    result = '$' + str(self.trial_data[-1][8])
                text = visual.TextStim(self.win, text=result, color='black', height=0.08)
                text.pos = (0, 0.75)
                text.draw()            
            
        # Draw the arrows
        for arrow in arrows:
            arrow.draw()

    def draw_confidence_scale(self):
        # Define confidence levels         
        confidence_text = f'¿Cuán seguro estás de que vas a ganar?'
        confidence_levels = ['Bastante', 'Algo', 'Poco', 'Nada']
        instructions = visual.TextStim(self.win, text=confidence_text, color='black', height=0.08, wrapWidth=1.7)
        instructions.pos = (0, 0.4)        

        # Draw confidence stims and images
        confidence_stims = []
        confidence_images = []
        initial_x = -0.4 * (len(confidence_levels) - 1) / 2 # Center the scale
        for i, level in enumerate(confidence_levels):
            # Draw the confidence levels
            confidence_stim = visual.TextStim(self.win, text=level, color='black', height=0.08)
            confidence_stim.pos = (initial_x + i * 0.4, 0)
            confidence_stims.append(confidence_stim)
            # Draw the confidence images
            image = visual.ImageStim(self.win, image=f'assets/key_{i + 1}.png')
            image.pos = (initial_x + i * 0.4, -0.3)
            confidence_images.append(image)            
        # Draw the instruction and confidence levels
        instructions.draw()            
        for stim in confidence_stims:
            stim.draw()
        for image in confidence_images:
            image.draw()

    def save_metadata(self, data):
        # Create the folder if it doesn't exist
        results_dir = os.path.dirname(self.metadata_file)
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        # Save the results:
        with open(self.metadata_file, 'a') as f:
            learn_list = [list(sublist) for sublist in data[1]] 
            reverse_list = [list(sublist) for sublist in data[4]] 
            f.write("learn_reward;learn_trials;refresh_trials;reverse_reward;reverse_trials\n")
            f.write(f"{data[0]};{learn_list};{data[2]};{data[3]};{reverse_list}\n")

    def read_metadata(self):
        # Check if the file exists
        if not os.path.exists(self.metadata_file):
            return None

        # Open the file for reading
        with open(self.metadata_file, 'r') as f:
            # Read the first line (header)
            header = f.readline().strip().split(';')
            
            # Read the second line (data)
            data = f.readline().strip()
            data_line = [eval(item) for item in data.split(';')]

            # Return a list containing the four saved values
            return data_line


    def save_results(self):
        # Create the folder if it doesn't exist
        results_dir = os.path.dirname(self.results_file)
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        # Save the results:
        with open(self.results_file, 'a') as f:
            f.write("cond;trial_n;trial_setup;chest_latency_ms;chest_sel;confidence_latency_ms;confidence_sel;hit;result;streak\n")
            for i, data in enumerate(self.trial_data):
                f.write(f"{data[0]};{data[1]};{data[2]};{data[3]};{data[4]};{data[5]};{data[6]};{data[7]};{data[8]};{data[9]}\n")          

if __name__ == "__main__": 
    # Request any relevant information needed:
    dlg = gui.Dlg(title="Información (MID)")
    dlg.addText("Por favor, ingresa ID, condición y parte del sujeto:")
    dlg.addField("Sujeto: ", "s")
    dlg.addField('Condición:', choices=["A", "B"])
    dlg.addField('Parte:', choices=["1", "2"])
    data = dlg.show()
    if dlg.OK:
        subject_id = data[0]
        exp_condition = data[1]
        experiment_part = int(data[2])
        task = MonetaryIncentiveDelayTask(subject_id, exp_condition, experiment_part)
        task.run()