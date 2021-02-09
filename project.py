# Rllib docs: https://docs.ray.io/en/latest/rllib.html

try:
    from malmo import MalmoPython
except:
    import MalmoPython

import sys
import time
import json
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import randint
import random

import gym, ray
from gym.spaces import Discrete, Box
from ray.rllib.agents import ppo


class CarrotCollector(gym.Env):

    def __init__(self, env_config):  
        # Static Parameters
        self.length = 20
        self.width = 50
        self.reward_density = .1
        self.penalty_density = .02
        self.obs_size = 5
        self.max_episode_steps = 100
        self.log_frequency = 10
        #color = "PINK"
        self.action_dict = {
            0: 'move 1',  # Move one block forward
            1: 'turn 1',  # Turn 90 degrees to the right
            2: 'turn -1',  # Turn 90 degrees to the left
            3: 'attack 1'  # Destroy block
        }

        # Rllib Parameters
        #self.action_space = Discrete(len(self.action_dict))
        self.action_space = Box(low = np.array([-1,-1]), high = np.array([1,1]), dtype=np.float32)
        self.observation_space = Box(0, 1, shape=(2 * self.obs_size * self.obs_size, ), dtype=np.float32)
        
        
        # Malmo Parameters
        self.agent_host = MalmoPython.AgentHost()
        try:
            self.agent_host.parse( sys.argv )
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agent_host.getUsage())
            exit(1)

        # DiamondCollector Parameters
        self.obs = None
        self.allow_break_action = False
        self.episode_step = 0
        self.episode_return = 0
        self.returns = []
        self.steps = []

    def reset(self):
        """
        Resets the environment for the next episode.

        Returns
            observation: <np.array> flattened initial obseravtion
        """
        # Reset Malmo
        world_state = self.init_malmo()

        # Reset Variables
        self.returns.append(self.episode_return)
        current_step = self.steps[-1] if len(self.steps) > 0 else 0
        self.steps.append(current_step + self.episode_step)
        self.episode_return = 0
        self.episode_step = 0

        # Log
        if len(self.returns) > self.log_frequency + 1 and \
            len(self.returns) % self.log_frequency == 0:
            self.log_returns()

        # Get Observation
        self.obs, self.allow_break_action = self.get_observation(world_state)

        return self.obs

    def step(self, action):
        """
        Take an action in the environment and return the results.

        Args
            action: <int> index of the action to take

        Returns
            observation: <np.array> flattened array of obseravtion
            reward: <int> reward from taking action
            done: <bool> indicates terminal state
            info: <dict> dictionary of extra information
        """

        # Get Action
        #command = self.action_dict[action]
        #if command != 'attack 1' or self.allow_break_action:
         #   self.agent_host.sendCommand(command)
         #   time.sleep(.2)
         #   self.episode_step += 1

        # Get Observation
        world_state = self.agent_host.getWorldState()

        #commandMove = 'move ' + str(action[0])
        #self.agent_host.sendCommand(commandMove)
        #time.sleep(0.2)

        
        # commandTurn = 'turn ' + str(action[1])
        # self.agent_host.sendCommand(commandTurn)
        # time.sleep(0.2)
        
        # if action[2] > 0 and self.allow_break_action:
        #     #self.agent_host.sendCommand('move 0')
        #     self.agent_host.sendCommand('turn 0')
        #     #self.agent_host.sendCommand('attack 1')
        #     for i in range(10):
        #         world_state = self.agent_host.getWorldState()
        #         self.obs, self.allow_break_action = self.get_observation(world_state)
        #         if self.allow_break_action:
        #             time.sleep(.1)
        #         else:
        #             break
            #self.agent_host.sendCommand('move 1')
            #self.agent_host.sendCommand('attack 0')
        
        command0 = "move " + str(action[0])
        command1 = "turn " + str(action[1])

        self.agent_host.sendCommand(command0)
        self.agent_host.sendCommand(command1)
        time.sleep(.2)
        
        self.episode_step += 1 

        world_state = self.agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:", error.text)
        self.obs, self.allow_break_action = self.get_observation(world_state) 

        # Get Done
        done = not world_state.is_mission_running 

        # Get Reward
        reward = 0
        for r in world_state.rewards:
            reward += r.getValue()
        self.episode_return += reward

        return self.obs, reward, done, dict()

    def get_mission_xml(self):
        setWallGlass_length = ""
        for z in range(-1,52):
            for y in range(2,5):
                setWallGlass_length += "<DrawBlock x='21' y='{}' z='{}' type='stained_glass' colour='PINK'/>".format(y,z)
                setWallGlass_length += "<DrawBlock x='-1' y='{}' z='{}' type='stained_glass' colour='PINK'/>".format(y,z)
        setWallGlass_width = ""
        for x in range(-1,22):
            for y in range(2,5):
                setWallGlass_length += "<DrawBlock x='{}' y='{}' z='51' type='stained_glass' colour='PINK' />".format(x,y)
                setWallGlass_length += "<DrawBlock x='{}' y='{}' z='-1' type='stained_glass' colour='PINK' />".format(x,y)

        carrot_map = [[10,1]]
        carrot_xml = "<DrawItem x='10' y ='2' z ='1' type ='carrot' />"
        carrot_location = [10,1]
        for i in range(0, self.width):
            rand = random.randint(0,2)
            if rand == 0:
                carrot_location[0] = carrot_location[0] - 1
                carrot_location[1] = carrot_location[1] + 1
            elif rand == 1:
                carrot_location[0] = carrot_location[0]
                carrot_location[1] = carrot_location[1] + 1
            else:
                carrot_location[0] = carrot_location[0] + 1
                carrot_location[1] = carrot_location[1] + 1
            
            if carrot_location[0] > 20:
                carrot_location[0] = 20

            temp = [carrot_location[0], carrot_location[1]]
            carrot_map.append(temp)    
            carrot_xml += "<DrawItem x='{}' y ='2' z ='{}' type ='carrot' />".format(carrot_location[0], carrot_location[1])
        
        mutton_xml = ""
        for i in range(0, self.length):
            for j in range(0, self.width):
                rand = random.uniform(0,1)
                if (rand < 0.15):
                    temp = [i, j]
                    if temp not in carrot_map:
                        temp_rand = random.randint(0,1)
                        if temp_rand == 0:
                            mutton_xml += "<DrawItem x='{}' y ='2' z ='{}' type ='mutton' />".format(temp[0],temp[1])
                        else:
                            mutton_xml += "<DrawItem x='{}' y ='2' z ='{}' type ='cooked_mutton' />".format(temp[0],temp[1])


        return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
                <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

                    <About>
                        <Summary>Carrot Collector</Summary>
                    </About>

                    <ServerSection>
                        <ServerInitialConditions>
                            <Time>
                                <StartTime>12000</StartTime>
                                <AllowPassageOfTime>false</AllowPassageOfTime>
                            </Time>
                            <Weather>clear</Weather>
                        </ServerInitialConditions>
                        <ServerHandlers>
                            <FlatWorldGenerator generatorString="3;7,2;1;"/>
                            <DrawingDecorator>''' + \
                                "<DrawCuboid x1='0' x2='{}' y1='2' y2='2' z1='0' z2='{}' type='air'/>".format(self.length, self.width) + \
                                "<DrawCuboid x1='0' x2='{}' y1='1' y2='1' z1='0' z2='{}' type='stone'/>".format(self.length, self.width) + \
                                setWallGlass_length + \
                                setWallGlass_width  + \
                                carrot_xml + \
                                mutton_xml + \
                                '''<DrawBlock x='0'  y='2' z='0' type='air' />
                                <DrawBlock x='10'  y='1' z='0' type='redstone_block' />
                            </DrawingDecorator>
                            <ServerQuitWhenAnyAgentFinishes/>
                        </ServerHandlers>
                    </ServerSection>

                    <AgentSection mode="Survival">
                        <Name>CarrotCollector</Name>
                        <AgentStart>
                            <Placement x="10.5" y="2" z="0.5" pitch="30" yaw="0"/>
                            <Inventory>
                                <InventoryItem slot="0" type="diamond_pickaxe"/>
                            </Inventory>
                        </AgentStart>
                        <AgentHandlers>
                            <RewardForCollectingItem>
                                <Item type = "carrot" reward ="5"/>
                                <Item type = "cooked_mutton" reward ="-1"/>
                                <Item type = "mutton" reward ="-2"/>
                            </RewardForCollectingItem>
                            <ContinuousMovementCommands/>
                            <ObservationFromFullStats/>
                            <ObservationFromRay/>
                            <ObservationFromGrid>
                                <Grid name="floorAll">
                                    <min x="-'''+str(int(self.obs_size/2))+'''" y="-1" z="-'''+str(int(self.obs_size/2))+'''"/>
                                    <max x="'''+str(int(self.obs_size/2))+'''" y="0" z="'''+str(int(self.obs_size/2))+'''"/>
                                </Grid>
                            </ObservationFromGrid>
                            <AgentQuitFromReachingCommandQuota total="'''+str(3*self.max_episode_steps)+'''" />
                            <AgentQuitFromTouchingBlockType>
                                <Block type="bedrock" />
                            </AgentQuitFromTouchingBlockType>
                        </AgentHandlers>
                    </AgentSection>
                </Mission>'''

    def init_malmo(self):
        """
        Initialize new malmo mission.
        """
        my_mission = MalmoPython.MissionSpec(self.get_mission_xml(), True)
        my_mission_record = MalmoPython.MissionRecordSpec()
        my_mission.requestVideo(800, 500)
        my_mission.setViewpoint(1)

        max_retries = 3
        my_clients = MalmoPython.ClientPool()
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

        for retry in range(max_retries):
            try:
                self.agent_host.startMission( my_mission, my_clients, my_mission_record, 0, 'DiamondCollector' )
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Error starting mission:", e)
                    exit(1)
                else:
                    time.sleep(2)

        world_state = self.agent_host.getWorldState()
        while not world_state.has_mission_begun:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            for error in world_state.errors:
                print("\nError:", error.text)

        return world_state

    def get_observation(self, world_state):
        """
        Use the agent observation API to get a flattened 2 x 5 x 5 grid around the agent. 
        The agent is in the center square facing up.

        Args
            world_state: <object> current agent world state

        Returns
            observation: <np.array> the state observation
            allow_break_action: <bool> whether the agent is facing a diamond
        """
        obs = np.zeros((2 * self.obs_size * self.obs_size, ))
        allow_break_action = False

        while world_state.is_mission_running:
            time.sleep(0.2)
            world_state = self.agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')

            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)

                # Get observation
                grid = observations['floorAll']
                for i, x in enumerate(grid):
                    obs[i] = x == 'diamond_ore' or x == 'lava'

                # Rotate observation with orientation of agent
                obs = obs.reshape((2, self.obs_size, self.obs_size))
                yaw = observations['Yaw']
                if yaw >= 247 and yaw < 293:
                    obs = np.rot90(obs, k=1, axes=(1, 2))
                elif yaw >= 327 or yaw < 23:
                    obs = np.rot90(obs, k=2, axes=(1, 2))
                elif yaw >= 67 and yaw < 113:
                    obs = np.rot90(obs, k=3, axes=(1, 2))
                obs = obs.flatten()

                allow_break_action = observations['LineOfSight']['type'] == 'diamond_ore'
                
                break

        return obs, allow_break_action

    def log_returns(self):
        """
        Log the current returns as a graph and text file

        Args:
            steps (list): list of global steps after each episode
            returns (list): list of total return of each episode
        """
        box = np.ones(self.log_frequency) / self.log_frequency
        returns_smooth = np.convolve(self.returns[1:], box, mode='same')
        plt.clf()
        plt.plot(self.steps[1:], returns_smooth)
        plt.title('Diamond Collector')
        plt.ylabel('Return')
        plt.xlabel('Steps')
        plt.savefig('returns.png')

        with open('returns.txt', 'w') as f:
            for step, value in zip(self.steps[1:], self.returns[1:]):
                f.write("{}\t{}\n".format(step, value))
        

if __name__ == '__main__':
    ray.init()
    trainer = ppo.PPOTrainer(env=CarrotCollector, config={
        'env_config': {},           # No environment parameters to configure
        'framework': 'torch',       # Use pyotrch instead of tensorflow
        'num_gpus': 0,              # We aren't using GPUs
        'num_workers': 0            # We aren't using parallelism
    })

    while True:
        print(trainer.train())
