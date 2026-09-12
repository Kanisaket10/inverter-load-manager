# Inverter Load Manager

A full-stack web application for managing appliance power consumption within a fixed inverter capacity of **800W**.

The system allows users to add, remove, turn ON/OFF appliances and automatically manages lower-priority appliances when the inverter reaches its capacity.

## Features

- Add appliances with:
  - Name
  - Wattage
  - Priority
- Turn appliances ON and OFF
- Delete appliances
- Track current inverter load
- Track remaining inverter capacity
- Automatically shed lower-priority appliances when required
- Automatically restore shed appliances when capacity becomes available
- Explicitly turned OFF appliances are not automatically restored
- Persistent data using SQLite
- REST APIs using FastAPI
- React-based frontend
- Handles concurrent state-changing requests using a lock

## Priority System

A smaller priority number means higher priority.

For example:

| Appliance | Wattage | Priority |
|-----------|---------|----------|
| Refrigerator | 200W | 1 |
| Fan | 100W | 2 |
| TV | 150W | 3 |
| Light | 60W | 4 |

If the inverter does not have enough capacity to turn on a high-priority appliance, the system can temporarily shed appliances with a **lower priority**.

For example, priority `1` can shed priority `2`, `3`, or `4`, but priority `3` cannot shed priority `1` or `2`.

## Appliance States

The application uses three states:

### RUNNING

The appliance is currently consuming inverter capacity.

### OFF

The appliance was explicitly turned OFF by the user.

An OFF appliance will not be automatically restored.

### SHED

The appliance was temporarily turned OFF by the system because a higher-priority appliance needed the available capacity.

A SHED appliance can automatically return to RUNNING when enough capacity becomes available.

## Automatic Load Management

The inverter has a maximum capacity of:

```text
800W