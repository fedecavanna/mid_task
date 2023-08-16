import random
from psychopy import visual, core, event, gui

def populate_trial_data():
    import random
    trials = 10
    seed_value = 42
    random.seed(seed_value)

    # defino las opciones posibles (0 o 1) y las probabilidades
    options = [0, 1]
    box_1_proba = [0.2, 0.8]
    box_2_proba = [0.5, 0.5]
    box_3_proba = [0.8, 0.2]

    # genero los 10 datos con las probabilidades dadas
    box_1 = random.choices(options, box_1_proba, k=trials)  
    box_2 = random.choices(options, box_2_proba, k=trials)  
    box_3 = random.choices(options, box_3_proba, k=trials)  
    
    result = []
    for i in range(10):
        result.append([box_1[i], box_2[i], box_3[i]])
    
    print('')

class MonetaryIncentiveDelayTask:

    def __init__(self, subject_id):
        # Variables de instancia:
        self.trials = 10
        self.reward_probabilities_learn = [0.8, 0.5, 0.2]
        self.reward_probabilities_reverse_learn = [0.2, 0.5, 0.8]
        self.subject_name = subject_id
        
        # visuales:
        self.win = visual.Window(fullscr=True, 
                                 # monitor='Dell precision',
                                 allowGUI=False, 
                                 color='gainsboro') # white
        self.fixation_cross = visual.TextStim(self.win, text='+', color='black', height=0.1)
        self.square_size = 0.2
        self.square_colors = ['gray', 'gray', 'gray']
        
        # guardado:
        self.trial_data = []
        self.results_file = f"results/{subject_id}.txt"

    def show_instructions(self):
        instruction_text = "Presiona cualquier tecla para comenzar el experimento."
        instructions = visual.TextStim(self.win, text=instruction_text, color='black')
        instructions.draw()
        self.win.flip()
        event.waitKeys()

    def run(self):
        iti = 1 # intervalo entre trials
        self.show_instructions()
        for trial in range(self.trials):
            reward_probability = random.choice(self.reward_probabilities)
            self.run_trial(reward_probability)
            core.wait(iti)
            
        self.save_results() 

    def run_trial(self, reward_probability):
        self.fixation_cross.draw()
        self.win.flip()
        core.wait(1)  # Fixation period

        squares = self.create_squares(reward_probability)
        self.win.flip()
        start_time = core.getTime()
        while True:
            keys = event.waitKeys(keyList=['left', 'down', 'right'])
            if keys[0] in ['left', 'down', 'right']:  # Check if a valid key was pressed
                break
            if core.getTime() - start_time > 5:
                selection = 'NS'
                break

        selected_square = ['left', 'down', 'right'].index(keys[0])
        result_text = '+1' if random.randint(1, 100) <= int(reward_probability * 100) else '-1'

        # Show feedback
        if result_text == '+1':
            color = 'green'
        else:
            color = 'red'

        feedback = visual.TextStim(self.win, text=result_text, color=color, height=0.1)
        feedback.draw()
        self.win.flip()
        core.wait(1)

        self.trial_data.append((selected_square, int((core.getTime() - start_time) * 1000), result_text))

    def create_squares(self, reward_probability):
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
            f.write("Trial_n;Latency_ms);box;hit\n")
            for i, data in enumerate(self.trial_data):
                hit = 1 if data[0] == data[2] else 0
                f.write(f"{i+1};{data[1]};{data[2]};{hit}\n")

if __name__ == "__main__":
    # Genero la información de los trials:
    populate_trial_data()
    
    # Pido toda información relevante que necesite:
    dlg = gui.Dlg(title="Información")
    dlg.addText("Por favor, ingresa el ID del sujeto:")
    dlg.addField("Sujeto: ", "s00")
    subject_id = dlg.show()
    if dlg.OK:
        task = MonetaryIncentiveDelayTask(subject_id)
        task.run()
