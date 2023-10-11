#!/usr/bin/env python3
import asyncio
import sys
from mavsdk import System
import pygame as gm
from mavsdk.offboard import PositionNedYaw, VelocityNedYaw, OffboardError

class DroneController:
    def __init__(self):
        self.drone = System()
        self.x = 0
        self.y = 0
        self.z = -2.5
        self.v = 0
        self.was_fly = False

    async def send(self, command):
        await self.drone.shell.send(command)

    async def observe_shell(self):
        async for output in self.drone.shell.receive():
            print(f"\n{output} ", end='', flush=True)

    async def init(self):
        await self.drone.connect("udp://:14540")
        print("Connecting to drone ...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("Connected to drone ..")
                break
        print("Waiting for GPS...")
        async for health in self.drone.telemetry.health():
            if health.is_home_position_ok and health.is_global_position_ok:
                print("Got GPS estimate and home position")
                break
        gm.init()
        gm.display.set_mode((300, 300))

    async def takeoff(self):
        in_air = await self.print_in_air()
        if in_air is False:
            asyncio.ensure_future(self.observe_shell())
            asyncio.ensure_future(self.send('commander takeoff'))
            await asyncio.sleep(5)
        elif in_air is True:
            pass

        
        print("Setting initial point ")
        await self.drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -2.5, 0.0))

        try:
                await self.drone.offboard.start()
                print("Starting OFFBOARD..")
                self.was_fly = True
        except OffboardError as error:
                print("Unable to start offboard")
                print(f'{error._result.result}')
                await self.drone.action.land()
                await self.drone.action.disarm()
                print("Offboard not starting !!!! /n Hence stopping takeoff")
                return
      

    async def land(self):
        try:
            await self.drone.offboard.stop()
            print("stopping offboard")
        except OffboardError as error:
            print("Unable to stop offboard")
            print(f'{error._result.result}')
        await self.drone.action.land()
        print("Landing...")
        if await self.print_in_air()!=True:
            self.x=0
            self.y=0
            self.z=-2.5
            self.v=0


    async def move(self):
        await self.drone.offboard.set_position_ned(PositionNedYaw(self.x, self.y, self.z, self.v))
        await asyncio.sleep(1)
        print(f'Moving to {self.x},{self.y},{self.z},{self.v} ')

    async def down(self):
        if await self.print_in_air() is True:
            await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 1.0, 0.0))
            await asyncio.sleep(1)
            print("Going Down 2m/s")
        else:
            print("Already landed")

    async def info(self):
        async for battery in self.drone.telemetry.battery():
            print(f"Battery: {battery.remaining_percent}")

    async def print_in_air(self):
        async for in_air in self.drone.telemetry.in_air():
            print(f'in_air {in_air}')
            return in_air

    async def control(self):
        gm.init()
        window = gm.display.set_mode((300, 300))
        run = True
        while run:
            for event in gm.event.get():
                if event.type == gm.QUIT:
                    run = False

            keys = gm.key.get_pressed()

            if keys[gm.K_t] and ((await self.print_in_air() is not True) or self.was_fly is False):
                await self.takeoff()
            elif keys[gm.K_l]:
                await self.land()
            elif keys[gm.K_UP]:
                self.x += 1
                await self.move()
            elif keys[gm.K_DOWN]:
                self.x -= 1
                await self.move()
            elif keys[gm.K_LEFT]:
                self.y -= 1
                await self.move()
            elif keys[gm.K_RIGHT]:
                self.y += 1
                await self.move()
            elif keys[gm.K_w]:
                self.z -= 1
                await self.move()
            elif keys[gm.K_s]:
                self.z += 1
                await self.move()
            elif keys[gm.K_d]:
                self.v += 20
                await self.move()
            elif keys[gm.K_a]:
                self.v -= 20
                await self.move()
            elif keys[gm.K_i]:
                await self.info()
            elif keys[gm.K_q]:
                run = False
                if await self.print_in_air() is True:

                    print("Stopping offboard .. ")
                    try:
                        await self.drone.offboard.stop()
                        await self.drone.action.land()
                        print("Landing..")

                    except OffboardError as error:
                        print("Unable to stop offboard")
                        print(f'{error._result.result}')
                        await self.drone.action.land()
                        print("Landing..")
                        await self.drone.action.disarm()
                        print("Disarming...")
                elif await self.print_in_air!=True:
                    pass
                
                raise asyncio.CancelledError  # Raise a custom exception

if __name__ == "__main__":
    drone_controller = DroneController()
    loop = asyncio.get_event_loop()

    try:
        # Initialize the drone
        loop.run_until_complete(drone_controller.init())

        # Start the control loop
        loop.run_until_complete(drone_controller.control())
    except asyncio.CancelledError:
          # Catch the exception and exit gracefully
        
    
        raise SystemExit
    
    # Close the event loop
   
