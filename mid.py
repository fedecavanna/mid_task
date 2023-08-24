# agregar señalización al eeg

import random
from psychopy import visual, core, event, gui
from pylsl import StreamInfo, StreamOutlet

class MonetaryIncentiveDelayTask:
    def populate_trial_data(self, n_trials, proba):
        # genero los datos con un seed fijo
        seed_value = -1 
        if (seed_value > 0):            
            random.seed(seed_value)
        
        # defino la ocurrencia de cada box acorde a las probabilidades dadas
        options = [0, 1]
        box_1 = random.choices(options, proba[0], k=n_trials)
        box_2 = random.choices(options, proba[1], k=n_trials)
        box_3 = random.choices(options, proba[2], k=n_trials)
        
        # armo los n_trials por box basándome en el array calculado previamente
        result = []
        for i in range(10):
            result.append([box_1[i], box_2[i], box_3[i]])
        print(result)
        return result

    def __init__(self, subject_id):     
        # https://pypi.org/project/pylsl/
        self.info = StreamInfo(name='MarkerStream', type='Markers', channel_count=1, 
                                channel_format='string', source_id='myuidw43536')
        self.outlet = StreamOutlet(self.info)
        
        # defino el reward de los cofres:
        self.trials = 10
        self.learn_trial = self.populate_trial_data(self.trials, [[0.8, 0.2], [0.5, 0.5], [0.2, 0.8]])
        self.reverse_trial = self.populate_trial_data(self.trials, [[0.2, 0.8], [0.5, 0.5], [0.8, 0.2]])        
        
        # defino variables visuales:
        self.win = visual.Window(fullscr=False, allowGUI=False, color='gainsboro') # white
        self.fixation_cross = visual.TextStim(self.win, text='+', color='black', height=0.1)
        self.square_size = 0.2
        self.square_colors = ['gray', 'gray', 'gray']
        
        # defino variables de guardado:
        self.trial_data = []
        self.results_file = f"results/{subject_id}.txt"

    def show_instructions(self):
        instruction_text = 'Presiona cualquier tecla para comenzar el experimento.'
        instructions = visual.TextStim(self.win, text=instruction_text, color='black')
        instructions.draw()
        self.win.flip()
        event.waitKeys()

    def run(self):
        self.outlet.push_sample('experiment_start') # EEG marker
        iti = 1 # intervalo entre trials (segundos)
        self.show_instructions()
        for i in range(self.trials):
            self.run_trial('learn', i+1, self.learn_trial[i]) # paso como parámetro el reward ya estimado de cada trial
            core.wait(iti)
        self.outlet.push_sample('experiment_end') # EEG marker
        self.save_results() 

    def run_trial(self, cond, trial_n, trial_reward):
        
        # Manejo el contador con el resultado total de ganancias-pérdidas:
        def calc_result(self, hit): 
            # obtengo el last count
            n = self.trial_data[-1][6] if len(self.trial_data) > 0 else 0
            # evalúo si agrego o resto y devuelvo
            res = n+1 if hit == 1 else n-1 
            return res
        
        self.outlet.push_sample('trial_start') # EEG marker
        
        # creo la cruz de fijación
        self.fixation_cross.draw()
        self.win.flip()
        self.outlet.push_sample('fixation_shown') # EEG marker
        core.wait(1) 
        
        # creo los cuadrados
        self.create_squares()
        self.win.flip()
        start_time = core.getTime()
        while True:
            keys = event.waitKeys(keyList=['left', 'down', 'right'])
            if keys[0] in ['left', 'down', 'right']:
                latency = int((core.getTime() - start_time) * 1000)
                self.outlet.push_sample('key_pressed') # EEG marker
                break

        # evalúo si le pegaron al box
        selected_square = ['left', 'down', 'right'].index(keys[0]) # devuelve 0, 1, 2
        hit = trial_reward[selected_square]
        result_text = '+1' if hit else '-1'

        # muestro el feedback
        color = 'red'
        if result_text == '+1':
            color = 'green'

        feedback = visual.TextStim(self.win, text=result_text, color=color, height=0.1)
        feedback.draw()
        self.win.flip()
        self.outlet.push_sample('feedback_shown') # EEG marker
        core.wait(1)

        # acumulo el resultado
        result = calc_result(self, hit)
        streak = self.trial_data[-1][7] + 1 if len(self.trial_data) > 0 and bool(hit) else hit 
        self.trial_data.append([cond, trial_n, trial_reward, latency, selected_square, hit, result, streak])
        trial_data_str = ', '.join(self.trial_data)
                       
        self.outlet.push_sample(trial_data_str) # EEG marker 
        self.outlet.push_sample('trial_end') # EEG marker 
    def create_squares(self):
        squares = []
        for i in range(3):
            square = visual.Rect(self.win, width=self.square_size, height=self.square_size, fillColor='gray')
            square.pos = ((i - 1) * 0.6, 0)
            squares.append(square)

        for square in squares:
            square.draw()

        return squares

    def save_results(self):
        with open(self.results_file, 'w') as f:
            f.write("cond;trial_n;trial_setup;latency_ms;selection;hit;result;streak\n")
            for i, data in enumerate(self.trial_data):
                f.write(f"{data[0]};{data[1]};{data[2]};{data[3]};{data[4]};{data[5]};{data[6]};{data[7]}\n")

if __name__ == "__main__": 
    # Pido toda información relevante que necesite:
    dlg = gui.Dlg(title="Información")
    dlg.addText("Por favor, ingresa el ID del sujeto:")
    dlg.addField("Sujeto: ", "s0")
    subject_id = dlg.show()
    if dlg.OK:
        task = MonetaryIncentiveDelayTask(subject_id[0])
        task.run()
