import asyncio
import random

class A(Exception):
    pass

async def fail():
    await asyncio.sleep(random.randint(0,5))
    if random.choice([True, False]):
        raise A("122")
    else:
        return 1

async def main():
    tasks = await asyncio.gather(*(asyncio.create_task(fail()) for _ in range(20)), return_exceptions=True)
#    await asyncio.wait(tasks)
    print(tasks)

asyncio.run(main())
