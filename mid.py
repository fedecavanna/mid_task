import random
from psychopy import visual, core, event

class MonetaryIncentiveDelayTask:
    def __init__(self, subject_name):
        self.subject_name = subject_name
        self.trials = 10
        self.reward_probabilities = [0.8, 0.5, 0.2]
        self.results_file = f"{subject_name}_results.txt"
        self.win = visual.Window(fullscr=True, allowGUI=False, color='white')
        self.fixation_cross = visual.TextStim(self.win, text='+', color='black', height=0.1)
        self.square_size = 0.2
        self.square_colors = ['gray', 'gray', 'gray']
        self.trial_data = []

    def run(self):
        self.show_instructions()
        for _ in range(self.trials):
            reward_probability = random.choice(self.reward_probabilities)
            self.run_trial(reward_probability)
            core.wait(1)  # Inter-trial interval

        self.save_results()

    def show_instructions(self):
        instruction_text = "Presiona cualquier tecla para comenzar el experimento."
        instructions = visual.TextStim(self.win, text=instruction_text, color='black')
        instructions.draw()
        self.win.flip()
        event.waitKeys()

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
            f.write("Trial;Latency (ms);Result;Correct\n")
            for i, data in enumerate(self.trial_data):
                f.write(f"{i+1};{data[1]};{data[2]};{1 if data[0] == data[2] else 0}\n")

if __name__ == "__main__":
    subject_name = input("Ingrese el nombre del sujeto: ")
    task = MonetaryIncentiveDelayTask(subject_name)
    task.run()
