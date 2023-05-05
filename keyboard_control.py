#!/usr/bin/env python3
import asyncio
from mavsdk import System
import pygame as gm
from mavsdk.offboard import (PositionNedYaw,VelocityNedYaw,OffboardError) 
x=0
y=0
z=-2.5
v=0

drone=System()
async def init():
    await drone.connect("udp://:14540")
    print("connecting to drone ..")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("connected to drone ..")
            break
    print("waiting fr GPS")
    async for health in drone.telemetry.health():
        if health.is_home_position_ok and health.is_global_position_ok:
            print(" got gps estimate and home position")
            break
gm.init()
window=gm.display.set_mode((300,300))
            
async def kes():
 
  run=True
  x=0
  y=0
  z=-2.5
  v=0
  while run== True:
    for event in gm.event.get():
            if event.type == gm.QUIT:
                run= False

    keys = gm.key.get_pressed()
    
    if keys[gm.K_t] and (await print_in_air(drone)!=True) :
        await takeoff()
    elif keys[gm.K_l]:
        await land()
    elif keys[gm.K_UP]:
       x=x+1
       await move(x,y,z,v)

    elif keys[gm.K_DOWN]:
       x=x-1
       await move(x,y,z,v)

    elif keys[gm.K_LEFT]:
       y=y-1
       await move(x,y,z,v)
    elif keys[gm.K_RIGHT]:
       y=y+1
       await move(x,y,z,v)
    elif keys[gm.K_w]:
       z=z-1
       await move(x,y,z,v)
    elif keys[gm.K_s]:
       z=z+1
       await move(x,y,z,v)
    elif keys[gm.K_d]:
       v=v+20
       await move(x,y,z,v)
    elif keys[gm.K_a]:
       v=v-20
       await move(x,y,z,v)
    elif keys[gm.K_i]:
       await info()
    elif keys[gm.K_q]:
       run=False
       if await print_in_air(drone)==True:
           print("stopping offboard .. ")
           try:
             await drone.offboard.stop()
  
           except OffboardError as error:
             print("unable to stop offboard")
             print(f'{error._result.result}')
             await drone.action.land()
             print("landing..")
             await drone.action.disarm()
             print("disarming...")
       elif await print_in_air(drone)!=True:
           return            
       print("program stopped by ESC")
       return
    
     

async def print_in_air(drone=drone):
 async for in_air in drone.telemetry.in_air():
   print(f'in_air{in_air}')
   return in_air
 



# TAKEOFF press T or t
async def takeoff():
   await drone.action.arm()
   print("arming drone..") 
   await asyncio.sleep(3)
   await drone.action.takeoff()
   print("taking off...")
   await asyncio.sleep(3)
   print("setting inital point ")
   await drone.offboard.set_position_ned(PositionNedYaw(0.0,0.0,-2.5,0.0))

   try:
    await drone.offboard.start()
    print("starting OFFBOARD..")
   except OffboardError as error:
       print("unable to start offboard")
       print(f'{error._result.result}')
       await drone.action.land()
       await drone.action.disarm()
       print("offboard not starting !!!! /n hence stopping takeoff")
       return
   

   
   
   #LANDING press L or l
async def land():
   try:
             await drone.offboard.stop()
  
   except OffboardError as error:
             print("unable to stop offboard")
             print(f'{error._result.result}')
   await drone.action.land()
   print("landing...")
   await drone.action.disarm()



async def move(x=x,y=y,z=z,v=v):
   await drone.offboard.set_position_ned(PositionNedYaw(x,y,z,v))
   await asyncio.sleep(1)
   print(f'moving to {x},{y},{z},{v} ')
   return


async def down():
 if await print_in_air==True:
  await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0,0.0,2.0,0.0))
  await asyncio.sleep(1)
  print("going Down 2m/s")
 else:
    print("already landed")  


async def info(drone=drone):
    async for battery in drone.telemetry.battery():
        print(f"Battery: {battery.remaining_percent}")
        
    return True
    
  
if __name__ == "__main__":
  loop=asyncio.get_event_loop()
  loop.run_until_complete(init())
  loop.run_until_complete(kes())
  loop.run_until_complete(print_in_air(drone))
  loop.run_until_complete(move(x,y,z,v))
  loop.run_until_complete(info(drone))
