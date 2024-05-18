import random
from collections import defaultdict
import math
import csv

K = 2.3
THRESHOLD = 0.1

class Agent:
    num_agents = 0

    def __init__(self):
        self.agent_id = Agent.num_agents
        Agent.num_agents += 1

        self.perceived_hardship = random.random()
        self.risk_aversion = random.random()
        self.active = False
        self.jail_term = 0
        self.heading = 0

    def __str__(self):
        return "Agent " + str(self.agent_id) + ": (a:" + str(self.active) + ", j:" + str(self.jail_term) + ")"
    
class Cop:
    numCops = 0

    def __init__(self):
        self.cop_id = Cop.numCops
        Cop.numCops += 1

    def __str__(self):
        return "Cop " + str(self.cop_id)

class RebellionManager:
    def __validate_value(self, name, value, expected_type, min_value, max_value):
        if not isinstance(value, expected_type):
            raise TypeError(f"{name} must be a {expected_type.__name__}.")
        if not (min_value <= value <= max_value):
            raise ValueError(f"{name} must be between {min_value} and {max_value}.")
    
    def __validate_parameters(self, initial_cop_density, initial_agent_density, vision, 
                                government_legitimacy, max_jail_term, movement_enabled):
        self.__validate_value("initial_cop_density", initial_cop_density, float, 0, 100)
        self.__validate_value("initial_agent_density", initial_agent_density, int, 0, 100)
        self.__validate_value("vision", vision, float, 0, 7)
        self.__validate_value("government_legitimacy", government_legitimacy, float, 0, 1)
        self.__validate_value("max_jail_term", max_jail_term, int, 0, 50)
        
        if not isinstance(movement_enabled, bool):
            raise TypeError("movement_enabled must be a boolean.")
        
        if initial_cop_density + initial_agent_density > 100:
            raise ValueError("The sum of initial_cop_density and initial_agent_density should not be greater than 100.")
    
    def __init__(self, max_pxcor=39, max_pycor=39):
        # initialise world
        self._tick = 0
        self._num_rows = max_pycor + 1
        self._num_cols = max_pxcor +  1
        self._coord_turtles = defaultdict(list)
        self._turtle_coords = dict()
        
        self._report = []

    def setup(self, initial_cop_density, initial_agent_density, vision, government_legitimacy=0.78, 
                max_jail_term=25, movement_enabled=False):
        
        # perform validation
        self.__validate_parameters(initial_cop_density, initial_agent_density, vision, 
                        government_legitimacy, max_jail_term, movement_enabled)
        
        # reset world
        self._tick = 0
        self._coord_turtles = defaultdict(list)
        self._turtle_coords = dict()
        
        # initialise other parameters
        self._num_cops = round(initial_cop_density * 0.01 * self._num_rows * self._num_cols)
        self._num_agents = round(initial_agent_density * 0.01 * self._num_rows * self._num_cols)
        self._vision = vision
        self._government_legitimacy = government_legitimacy
        self._max_jail_term = max_jail_term
        self._movement_enabled = movement_enabled

        # define our neighbours dictionary which maps a coordinate to its set or neighbour coordinates
        self.__init_coord_neighbours()
        
        # initialise empty grid spots
        available_patches = []
        for i in range(self._num_rows):
            for j in range(self._num_cols):
                available_patches.append((i, j))

        for _ in range(self._num_cops):
            # get random empty spot
            index = random.randrange(len(available_patches))
            (row, col) = available_patches.pop(index)

            # generate a new cop
            cop = Cop()

            self._coord_turtles[(row, col)] = [cop]
            self._turtle_coords[cop] = (row, col)

        for _ in range(self._num_agents):
            # get random empty spot
            index = random.randrange(len(available_patches))
            (row, col) = available_patches.pop(index)

            # generate a new agent
            agent = Agent()

            self._coord_turtles[(row, col)] = [agent]
            self._turtle_coords[agent] = (row, col)

        # start new report
        self._report = [{"tick": 0, "quiet": self._num_agents, "jailed": 0, "active": 0}]

        self.__print_patches()

    def __init_coord_neighbours(self):
        def distance(source, target):
            # distance calculation which takes into consideration wrapping
            dx = abs(source[0] - target[0])
            dy = abs(source[1] - target[1])
            
            # Adjust distances for wrapping
            if dx > self._num_rows / 2:
                dx = self._num_rows - dx
            if dy > self._num_cols / 2:
                dy = self._num_cols - dy
            
            return math.sqrt(dx**2 + dy**2)

        neighbours_dict = defaultdict(list)
        coord_centres = dict()

        for i in range(self._num_rows):
            for j in range(self._num_cols):
                # Netlogo distance calculates from the centre
                coord_centres[(i, j)] = [i + 0.5, j + 0.5]
        
        for coord, centre in coord_centres.items():
            # the Netlogo implementation for in-radius doesn't exclude the coord
            for other_coord, other_centre in coord_centres.items():

                if distance(centre, other_centre) <= self._vision:
                    neighbours_dict[coord].append(other_coord)
            
        self._coord_neighbours = neighbours_dict

    def __print_patches(self):
        print(f"Tick = {self._tick}\nNum Cops = {self._num_cops}\nNum Agents = {self._num_agents}\n")

        for i in range(self._num_rows):
            str_row = ""
            for j in range(self._num_cols):
                str_cell = ""       

                if self._coord_turtles[(i, j)] != []:
                    for char in self._coord_turtles[(i, j)]:
                        str_cell += str(char) + ", "
                else:
                    str_cell += "Empty"

                str_row += "(" + str_cell + ") "

            print("[" + str_row + "]")

        print("")

    def go(self, mute=False):
        for turtle, turtle_coord in self._turtle_coords.items():
            # Rule M: Move to a random site within your vision
            if (isinstance(turtle, Agent) and turtle.jail_term == 0) or isinstance(turtle, Cop):
                self.__move(turtle, turtle_coord)

            # Rule A: Determine if each agent should be active or quiet
            if (isinstance(turtle, Agent) and turtle.jail_term == 0):
                turtle.active = self.__determine_behaviour(turtle)

            # Rule C: Cops arrest a random active agent within their radius
            if isinstance(turtle, Cop):
                self.__enforce(turtle, turtle_coord)

        # Jailed agents get their term reduced at the end of each clock tick
        # The Netlogo implementation doesn't account for freshly jailed agents
        for turtle in self._turtle_coords.keys():
            if isinstance(turtle, Agent):
                turtle.jail_term = max(0, turtle.jail_term - 1)

        self._tick += 1

        # update report
        quiet = 0
        jailed = 0
        active = 0
        for turtle in self._turtle_coords.keys():
            if isinstance(turtle, Agent):
                if turtle.active:
                    active += 1
                else:
                    quiet += 1

                if turtle.jail_term != 0:
                    jailed += 1
        self._report.append({"tick": self._tick, "quiet": quiet, "jailed": jailed, "active": active})
        
        # print new state
        if not mute:
            self.__print_patches()

    def __move_turtle(self, turtle, source, destination):
        # add turtle to destination
        self._coord_turtles[destination].append(turtle)

        # remove from source
        self._coord_turtles[source] = [c for c in self._coord_turtles[source] if c != turtle]

        # change turtle location
        self._turtle_coords[turtle] = destination
        
    def __move(self, turtle, coord):
        if self._movement_enabled or isinstance(turtle, Cop):
            # move to a patch in vision
            # candidate patches are empty or contain only jailed agents
            targets = []
            for neighbour_i, neighbour_j in self._coord_neighbours[coord]:
                turtles_at_neighbour = self._coord_turtles[(neighbour_i, neighbour_j)]

                if turtles_at_neighbour == []:
                    targets.append((neighbour_i, neighbour_j))
                else:
                    # check if neighbour cell contains only jailed agents
                    valid_square = True

                    for other_turtle in turtles_at_neighbour:
                        if not isinstance(other_turtle, Agent) or other_turtle.jail_term == 0:
                            valid_square = False
                            break
                    
                    if valid_square:
                        targets.append((neighbour_i, neighbour_j))

            # select a target location for our turtle to move to
            if targets:
                destination = random.choice(targets)
                self.__move_turtle(turtle, coord, destination)
       
    def __determine_behaviour(self, turtle: Agent):
        # calculate grievance
        grievance = turtle.perceived_hardship * (1 - self._government_legitimacy)

        # estimate arrest probability
        c = len([x for x in self._turtle_coords if isinstance(turtle, Cop)])
        a = 1 + len([x for x in self._turtle_coords if isinstance(turtle, Agent)])
        estimated_arrest_probability = 1 - math.exp(-K * math.floor(c / a))

        return (grievance - turtle.risk_aversion * estimated_arrest_probability) > THRESHOLD
            
    def __enforce(self, turtle: Cop, coord):
        suspects = []
        
        # gather suspects of active agents from neighbours near turtle
        for neighbour_coord in self._coord_neighbours[coord]:
            for neighbour in self._coord_turtles[neighbour_coord]:
                if isinstance(neighbour, Agent) and neighbour.active:
                    suspects.append((neighbour, neighbour_coord))

        # choose suspect
        if suspects:
            suspect, suspect_coord = random.choice(suspects)

            # move cop to suspect
            self.__move_turtle(turtle, coord, suspect_coord)

            # arrest suspect
            suspect.active = False
            suspect.jail_term = random.randrange(self._max_jail_term)

    def update_government_legitimacy(self, government_legitimacy):
        self._government_legitimacy = government_legitimacy

    def update_max_jail_term(self, max_jail_term):
        self._max_jail_term = max_jail_term

    def update_movement_enabled(self, movement_enabled):
        self._movement_enabled = movement_enabled

    def generate_report(self):
        if self._report == []:
            print("Nothing to Report")
            return

        print("Saving to csv...")

        # Open a file in write mode.
        with open('test.csv', 'w') as f:
            f.write(','.join(self._report[0].keys()))
            f.write('\n') # Add a new line
            for row in self._report:
                # Write the values in a row.
                f.write(','.join(str(x) for x in row.values()))
                f.write('\n') # Add a new line

        print("Done !!")

def main():
    """
    WHY WE CANT REPLICATE THE EXACT BEHVAIOUR OF THE NETLOGO MODEL
    - we don't know exactly how one-of randomly selects an item from a list
    - we don't know the exact order that Netlogo iterates through its turtles
        - the rebellion model does not operate asynchronously (you can look at the code) and the movement
          method of each turtle depends on the ordering that turtles are updated

    ASSUMPTION/ACTIONS WE HAVE TO MAKE TO PROCEED
    - the distance function used includes wrapping and uses euclidean distance
    - make the update function asynchronous across the turtles
        - if we don't, we will get unexpected behaviours such as mutiple unjailed agents and cops at the same coord

        
    Below provides a sample of how the RebellionManager may be used to simulate rebellion within a population
    """
    # intialise seed for random number generator
    random.seed(2024)

    # initialise manager and size of the world 
    manager = RebellionManager(max_pxcor=5, max_pycor=5)

    # intialise world parameters
    manager.setup(initial_cop_density=27.4, initial_agent_density=20, vision=7.0, max_jail_term=10)

    # start simulation
    NUM_TICKS_TO_SIMULATE = 100
    for tick in range(NUM_TICKS_TO_SIMULATE):
        manager.go()
        
        # enable agent movement halfway through
        if tick == NUM_TICKS_TO_SIMULATE // 2:
            manager.update_movement_enabled(True)

    # generate report from simulation
    manager.generate_report()

if __name__ == '__main__':
    main()