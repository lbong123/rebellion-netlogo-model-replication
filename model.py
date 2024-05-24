import random
from collections import defaultdict
import math
import statistics as st

K = 2.3
THRESHOLD = 0.1

class Agent:
    """
    A class to replicate Agents within our population
    """

    num_agents = 0 # a counter to generate agent ids

    def __init__(self):
        """
        Generates a new Agent with randomised hardship and risk aversion
        """
        self.agent_id = Agent.num_agents # the unique identifier of the agent
        Agent.num_agents += 1

        self.perceived_hardship = random.random() # the perceived hardship
        self.risk_aversion = random.random() # the risk aversion of the agent
        self.active = False # whether the agent is active
        self.jail_term = 0 # how many ticks left before leaving jail

    def __str__(self):
        return "Agent " + str(self.agent_id) + ": (a:" + str(self.active) + ", j:" + str(self.jail_term) + ")"
    
    def __eq__(self, other):
        return isinstance(other, Agent) and self.agent_id == other.agent_id
    
    def __hash__(self):
        return hash("A:" + str(self.agent_id))
    
class Cop:
    """
    A class to replicate Cops within our population
    """
    numCops = 0 # a counter to generate cop ids

    def __init__(self):
        """
        Generates a new cop
        """
        self.cop_id = Cop.numCops # the unique identifier for the cop
        Cop.numCops += 1

    def __str__(self):
        return "Cop " + str(self.cop_id)
    
    def __eq__(self, other):
        return isinstance(other, Cop) and self.cop_id == other.cop_id
    
    def __hash__(self):
        return hash("C:" + str(self.cop_id))

class RebellionManager:
    """
    The coordinator the systems simulation and report generation. It is additionally the only
    interface and class intended to be directly utilised by the user.
    """
    def __validate_value(self, name, value, expected_type, min_value, max_value):
        """
        Validates a value of any type

        Parameters
        ----------
        name : string
            the name of the parameter
        value : any
            the value we are trying to validate
        expected_type : any
            the type of the value we are expecting
        min_value : _type_
            for range validations
        max_value : _type_
            for range validations

        Raises
        ------
        TypeError
            _description_
        ValueError
            _description_
        """
        if not isinstance(value, expected_type):
            raise TypeError(f"{name} must be a {expected_type.__name__}.")
        if not (min_value <= value <= max_value):
            raise ValueError(f"{name} must be between {min_value} and {max_value}.")
    
    def __validate_parameters(self, initial_cop_density, initial_agent_density, vision, 
                                government_legitimacy, max_jail_term, movement_enabled):
        """
        Validates the system parameters during setup

        Parameters
        ----------
        initial_cop_density : any
            the initial cop density
        initial_agent_density : any
            the initial agent density
        vision : any
            the vision
        government_legitimacy : any
            the government legitimacy
        max_jail_term : any
            the max jail term
        movement_enabled : any
            if movement is enabled

        Raises
        ------
        TypeError
            _description_
        ValueError
            _description_
        """

        # validate numeric values
        self.__validate_value("initial_cop_density", initial_cop_density, float, 0, 100)
        self.__validate_value("initial_agent_density", initial_agent_density, int, 0, 100)
        self.__validate_value("vision", vision, float, 0, 7)
        self.__validate_value("government_legitimacy", government_legitimacy, float, 0, 1)
        self.__validate_value("max_jail_term", max_jail_term, int, 0, 50)
        
        # validates movement
        if not isinstance(movement_enabled, bool):
            raise TypeError("movement_enabled must be a boolean.")
        
        if initial_cop_density + initial_agent_density > 100:
            raise ValueError("The sum of initial_cop_density and " + 
                                "initial_agent_density should not be greater than 100.")
    
    def __init__(self, max_pxcor=39, max_pycor=39):
        """
        The constructor for our rebellion manager

        Parameters
        ----------
        max_pxcor : int, optional
            the max x coordinate of the grid, by default 39
        max_pycor : int, optional
            the max y coordinate of the grid, by default 39
        """
        # initialise world
        self._tick = 0 # counter
        self._num_rows = max_pycor + 1 # x coordinate range
        self._num_cols = max_pxcor +  1 # y coordinate range
        # a mapping between a coordinate and the turtles that exist at the coordinate
        self._coord_turtles = defaultdict(list)
        # a mapping between a turtle and its coordinate on the grid
        self._turtle_coords = dict()
        
        # stores the state of the system at each tick
        self._report = []

    def setup(self, initial_cop_density, initial_agent_density, vision, government_legitimacy=0.82, 
                max_jail_term=25, movement_enabled=False, aggregate_greivance=False):
        """
        Setups the turtles on the grid and resets all necessary counters

        Parameters
        ----------
        initial_cop_density : any
            the initial cop density
        initial_agent_density : any
            the initial agent density
        vision : any
            the vision
        government_legitimacy : float, optional
            the government legitimacy, by default 0.82
        max_jail_term : int, optional
            the max jail term, by default 25
        movement_enabled : bool, optional
            whether movement is enabled, by default False
        aggregate_greivance : bool, optional
            whether aggregate greivance is enabled, by default False
        """
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

        # define our neighbours dictionary which maps a coordinate to its set of neighbours
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

            # shift perceived hardships according to neighbours by a scale
            # this will exacerbate the aggregate greivances calculations during the agent behaviour 
            # update step
            if aggregate_greivance:
                neighbour_hardships = []
                
                for neighbour_coord in self._coord_neighbours[(row, col)]:
                    for neighbour in self._coord_turtles[neighbour_coord]:
                        if isinstance(neighbour, Agent):
                            neighbour_hardships.append(neighbour.perceived_hardship)

                agent.perceived_hardship += (0.1 * 
                                             ((sum(neighbour_hardships) 
                                               / max(len(neighbour_hardships), 0.0001)) 
                                               - agent.perceived_hardship))

            self._coord_turtles[(row, col)] = [agent]
            self._turtle_coords[agent] = (row, col)

        # start new report
        self._report = [{"tick": 0, "quiet": self._num_agents, "jailed": 0, "active": 0}]

        self.__print_patches()

    def __init_coord_neighbours(self):
        """
        Maps each grid coordinate to its set of neighbour coordinates based on toroidal wrapping
        and euclidean distance from the centre of each cell 
        """
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
        
        # stores the mapping for later use
        self._coord_neighbours = neighbours_dict

    def __print_patches(self):
        """
        Testing function to visualise the grid
        """
        print(f"Tick = {self._tick}\nNum Cops = {self._num_cops}" +
                                            "\nNum Agents = {self._num_agents}\n")

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

    def go(self, mute=False, shift_perceived_hardship=False, aggregate_greivance=False):
        """
        Simulates one tick in time and optionally prints the new grid configuration

        Parameters
        ----------
        mute : bool, optional
            whether to mute board printing, by default False
        shift_perceived_hardship : bool, optional
            whether scale shifting is enabled, by default False
        aggregate_greivance : bool, optional
            whether aggregate grievance is enabled, by default False
        """
        # create a randomly shuffled set of turtle coords
        shuffled_turtle_coords = list(self._turtle_coords.items())
        random.shuffle(shuffled_turtle_coords)
        
        for turtle, turtle_coord in shuffled_turtle_coords:
            # Rule M: Move to a random site within your vision
            if (isinstance(turtle, Agent) and turtle.jail_term == 0) or isinstance(turtle, Cop):
                self.__move(turtle, turtle_coord)

            # Rule A: Determine if each agent should be active or quiet
            if (isinstance(turtle, Agent) and turtle.jail_term == 0):
                turtle.active = self.__determine_behaviour(turtle, shift_perceived_hardship, aggregate_greivance)

            # Rule C: Cops arrest a random active agent within their radius
            if isinstance(turtle, Cop):
                self.__enforce(turtle, self._turtle_coords[turtle])

        # Jailed agents get their term reduced at the end of each clock tick
        # The Netlogo implementation doesn't account for freshly jailed agents
        for turtle in self._turtle_coords.keys():
            if isinstance(turtle, Agent):
                turtle.jail_term = max(0, turtle.jail_term - 1)

        # increment our tick
        self._tick += 1

        # update report
        quiet = 0
        jailed = 0
        active = 0
        for turtle in self._turtle_coords.keys():
            if isinstance(turtle, Agent):
                if turtle.jail_term != 0:
                    jailed += 1
                elif turtle.active:
                    active += 1
                else:
                    quiet += 1

        self._report.append({"tick": self._tick, "quiet": quiet, "jailed": jailed, "active": active})
        
        # print new state
        if not mute:
            self.__print_patches()

    def __move_turtle(self, turtle, source, destination):
        """
        Helper function which moves a turtle from one coordinate to another

        Parameters
        ----------
        turtle : Agent or Cop
            the turtle we are moving
        source : _type_
            the source coordinate
        destination : _type_
            the destination coordinate
        """
        # add turtle to destination
        self._coord_turtles[destination].append(turtle)

        # remove from source
        self._coord_turtles[source] = [c for c in self._coord_turtles[source] if c != turtle]
        # change turtle location
        self._turtle_coords[turtle] = destination
        
    def __move(self, turtle, coord):
        """
        Helper function to help simulate a tick in the go function, moves a turtle to a valid space

        Parameters
        ----------
        turtle : Agent or Cop
            the turtle being moved
        coord : (int, int)
            the current coordinate of the turtle
        """
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
       
    def __determine_behaviour(self, turtle: Agent, shift_perceived_hardship, aggregate_greivance):
        """
        Helper function to help simulate a tick in the go function,determines an agents activeness

        Parameters
        ----------
        turtle : Agent
            the agent
        shift_perceived_hardship : bool
            whether scale shifting is enabled
        aggregate_greivance : bool
            whether aggregate greivance is enabled

        Returns
        -------
        bool
            whether the agent should become active
        """
        # shift perceived hardship over time to either 0 or 1
        if shift_perceived_hardship:
            turtle.perceived_hardship += 0.1 * (turtle.perceived_hardship - 0.5)
            
            # ensure we dont go out of bounds
            if turtle.perceived_hardship < 0:
                turtle.perceived_hardship = 0
            if turtle.perceived_hardship > 1:
                turtle.perceived_hardship = 1

        # get greivance of all neighbour agents
        if aggregate_greivance:
            current_turtle_location = self._turtle_coords[turtle]
            neighbour_grievances = []

            for neighbour_coord in self._coord_neighbours[current_turtle_location]:
                for neighbour in self._coord_turtles[neighbour_coord]:
                    if isinstance(neighbour, Agent):
                        neighbour_grievances.append(neighbour.perceived_hardship * (1 - self._government_legitimacy))

            grievance = sum(neighbour_grievances) / len(neighbour_grievances)
        else:
            # calculate grievance using standard formula
            grievance = turtle.perceived_hardship * (1 - self._government_legitimacy)

        # estimate arrest probability
        c = 0
        a = 1
        for neighbour_coord in self._coord_neighbours[self._turtle_coords[turtle]]:
            for neighbour in self._coord_turtles[neighbour_coord]:
                if isinstance(neighbour, Cop):
                    c += 1
                if isinstance(neighbour, Agent) and neighbour.active:
                    a += 1

        estimated_arrest_probability = 1 - math.exp(-K * math.floor(c / a))

        return (grievance - turtle.risk_aversion * estimated_arrest_probability) > THRESHOLD
            
    def __enforce(self, turtle: Cop, coord):
        """
        Helper function to help simulate a tick in the go function, attempts to perform an arrest

        Parameters
        ----------
        turtle : Cop
            the cop performing the arrest
        coord : _type_
            the coordinate of the cop
        """
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
            if coord != self._turtle_coords[turtle]:
                print("Failed")
                print(coord)
                print(self._turtle_coords[turtle])
            self.__move_turtle(turtle, coord, suspect_coord)

            # arrest suspect
            suspect.active = False
            suspect.jail_term = random.randrange(self._max_jail_term)

    def update_government_legitimacy(self, government_legitimacy):
        """
        updates the government legitimacy parameter after setup has been performed

        Parameters
        ----------
        government_legitimacy : float
            the governement legitimacy
        """
        self.__validate_value("government_legitimacy", government_legitimacy, float, 0, 1)
        self._government_legitimacy = government_legitimacy

    def update_max_jail_term(self, max_jail_term):
        """
        updates the max jail term parameter after setup has been performed

        Parameters
        ----------
        max_jail_term : int
            the max jail term
        """
        self.__validate_value("max_jail_term", max_jail_term, int, 0, 50)
        self._max_jail_term = max_jail_term

    def update_movement_enabled(self, movement_enabled):
        """
        updates the movement boolean parameter after setup has been performed

        Parameters
        ----------
        movement_enabled : bool
            is movement enabled
        """
        if not isinstance(movement_enabled, bool):
            raise TypeError("movement_enabled must be a boolean.")
        self._movement_enabled = movement_enabled

    def generate_report(self):
        """
        Generates a report of the combined statistics from the simulation thus far
        """
        if self._report == []:
            print("Nothing to Report")
            return

        # generating statstics
        quiet = []
        jailed = []
        active = []

        for x in self._report:
            quiet.append(x["quiet"])
            jailed.append(x["jailed"])
            active.append(x["active"])

        print("Generating statistics for the run")
        print(f"quiet:\n mean = {st.mean(quiet)}" + 
                            f", std = {st.stdev(quiet)}, max = {max(quiet)}, min = {min(quiet)}")
        print(f"jailed:\n mean = {st.mean(jailed)}" + 
                            f", std = {st.stdev(jailed)}, max = {max(jailed)}, min = {min(jailed)}")
        print(f"active:\n mean = {st.mean(active)}" + 
                        f", std = {st.stdev(active)}, max = {max(active)}, min = {min(active)}\n")

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
        - the rebellion model does not operate asynchronously (you can look at the code) and the 
          movement method of each turtle depends on the ordering that turtles are updated

    ASSUMPTION/ACTIONS WE HAVE TO MAKE TO PROCEED
    - the distance function used includes wrapping and uses euclidean distance
    - make the update function asynchronous across the turtles
        - if we don't, we will get unexpected behaviours such as mutiple unjailed agents and cops 
          at the same coord

        
    Below provides a sample of how the RebellionManager may be used to simulate rebellion within a
    population
    """
    # intialise seed for random number generator
    random.seed(12)

    # initialise manager and size of the world 
    manager = RebellionManager(max_pxcor=39, max_pycor=39)

    # intialise world parameters
    manager.setup(initial_cop_density=4.0, initial_agent_density=70, vision=7.0, 
                                            max_jail_term=30, movement_enabled=True)

    # start simulation
    NUM_TICKS_TO_SIMULATE = 100
    for tick in range(NUM_TICKS_TO_SIMULATE):
        manager.go(mute=True, aggregate_greivance=True)

    # generate report from simulation
    manager.generate_report()

if __name__ == '__main__':
    main()