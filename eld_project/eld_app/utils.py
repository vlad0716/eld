from datetime import datetime, timedelta

def parse_datetime(datetime_str):
    return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))

def detect_hos_violations(eld_data_list):
    violations = []

    for data in eld_data_list:
        driver_id = data.get('driverId')
        duty_status = data.get('dutyStatus')
        duty_status_start_time = datetime.fromisoformat(data.get('dutyStatusStartTime').replace('Z', '+00:00'))
        shift_work_minutes = data.get('shiftWorkMinutes')
        shift_drive_minutes = data.get('shiftDriveMinutes')
        cycle_work_minutes = data.get('cycleWorkMinutes')
        max_shift_work_minutes = data.get('maxShiftWorkMinutes')
        max_shift_drive_minutes = data.get('maxShiftDriveMinutes')
        max_cycle_work_minutes = data.get('maxCycleWorkMinutes')
        time_zone = data.get('homeTerminalTimeZoneIana')

        # Check shift work time violation
        shift_work_violation = shift_work_minutes > max_shift_work_minutes
        shift_drive_violation = shift_drive_minutes > max_shift_drive_minutes
        cycle_work_violation = cycle_work_minutes > max_cycle_work_minutes

        violations.append({
            'driver_id': driver_id,
            'shift_work_violation': shift_work_violation,
            'shift_drive_violation': shift_drive_violation,
            'cycle_work_violation': cycle_work_violation,
        })

    return violations

# def check_property_sleeper_berth(violations, off_duty_periods):
#     """
#     Ensures property-carrying drivers do not violate the Sleeper Berth Provision.
#     """
#     # total_off_duty = sum((period['duration'] for period in off_duty_periods), timedelta())
#     valid_period = any(period['duration'] >= timedelta(hours=2) for period in off_duty_periods) and total_off_duty >= timedelta(hours=7)

#     for period in off_duty_periods:
#         if period['duration'] < timedelta(hours=10) or not valid_period:
#             found = False
#             for violation in violations:
#                 if violation.get('driverId') == period["driverId"]:
#                     violation['violation'] = 'Failed Sleeper Berth Provision'
#                     found = True
#                     break
#             if not found:
#                 violations.append({'driverId': period["driverId"], 'violation': 'Failed Sleeper Berth Provision'})

# def check_passenger_sleeper_berth(violations, off_duty_periods):
#     """
#     Ensures passenger-carrying drivers do not violate the Sleeper Berth Provision.
#     """
#     # total_off_duty = sum((period['duration'] for period in off_duty_periods), timedelta())
#     valid_period = any(period['duration'] >= timedelta(hours=2) for period in off_duty_periods) and total_off_duty >= timedelta(hours=6)
#     for period in off_duty_periods:
#         if period['duration'] < timedelta(hours=8) or not valid_period:
#             found = False
#             for violation in violations:
#                 if violation.get('driverId') == period["driverId"]:
#                     violation['violation'] = 'Failed Sleeper Berth Provision'
#                     found = True
#                     break
#             if not found:
#                 violations.append({'driverId': period["driverId"], 'violation': 'Failed Sleeper Berth Provision'})

        
MAX_DRIVING_HOURS_BEFORE_BREAK = timedelta(hours=8)
MAX_DRIVING_HOURS_IN_A_DAY = timedelta(hours=11)
MAX_ON_DUTY_HOURS_IN_A_DAY = timedelta(hours=14)
MAX_ON_DUTY_HOURS_IN_8_DAYS = timedelta(hours=70)

def calculate_schedule_with_sleeper_berth(pickup_time_str, dropoff_time_str, driver_type='property'):
    # Convert strings to datetime objects
    pickup_time = datetime.fromisoformat(pickup_time_str.replace('Z', '+00:00'))
    dropoff_time = datetime.fromisoformat(dropoff_time_str.replace('Z', '+00:00'))

    schedule = []
    current_time = pickup_time
    spent_sleeper_berth = False
    spent_off_duty_break = False

    if driver_type == 'property':
        min_sleeper_berth_hours = 7
        total_off_duty_hours = 10
    elif driver_type == 'passenger':
        min_sleeper_berth_hours = 8
        total_off_duty_hours = 8
    else:
        raise ValueError("Unknown driver type. Must be 'property' or 'passenger'.")

    # Function to add duty period to schedule
    def add_duty_period(start_time, end_time, duty_status):
        schedule.append({
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duty_status': duty_status,
        })

    while current_time < dropoff_time:
        # First drive period
        drive_end_time = min(current_time + MAX_DRIVING_HOURS_BEFORE_BREAK, dropoff_time)
        add_duty_period(current_time, drive_end_time, 'D')
        current_time = drive_end_time

        if current_time >= dropoff_time:
            break

        # Off-duty periods according to sleeper berth provision 
        if not spent_sleeper_berth:
            # Spend at least 7 or 8 hours in the sleeper berth depending on driver type
            sleeper_berth_end_time = min(current_time + timedelta(hours=min_sleeper_berth_hours), dropoff_time)
            add_duty_period(current_time, sleeper_berth_end_time, 'SB')
            current_time = sleeper_berth_end_time
            spent_sleeper_berth = True
        elif not spent_off_duty_break:
            # Spend at least 2 hours off-duty or in sleeper berth
            off_duty_end_time = min(current_time + timedelta(hours=2), dropoff_time)
            add_duty_period(current_time, off_duty_end_time, 'OFF')
            current_time = off_duty_end_time
            spent_off_duty_break = True

        if spent_sleeper_berth and spent_off_duty_break:
            # Reset for next driving period
            spent_sleeper_berth = False
            spent_off_duty_break = False

    

    # Ensure all sleeper berth periods add up to at least 7/8 hours in total
    sleeper_berth_time = sum(
        (datetime.fromisoformat(entry['end_time']) - datetime.fromisoformat(entry['start_time'])).total_seconds()
        for entry in schedule if entry['duty_status'] == 'SB'
    ) / 3600.0

    
    # Ensure total off-duty time including sleeper berth adds up to at least 10 hours for property-carrying
    total_off_duty_time = sum(
        (datetime.fromisoformat(entry['end_time']) - datetime.fromisoformat(entry['start_time'])).total_seconds()
        for entry in schedule if entry['duty_status'] in ['SB', 'OFF']
    ) / 3600.0


    if driver_type == 'property':
        if sleeper_berth_time < 7 or total_off_duty_time < 10:
            raise ValueError("Total sleeper berth time must be at least 7 hours and total off-duty time must be at least 10 hours")
    elif driver_type == 'passenger':
        if sleeper_berth_time < 8:
            raise ValueError("Total sleeper berth time must be at least 8 hours")

    return schedule


def validate_hos_with_conditions(pickup_time_str, dropoff_time_str, eld_data_list, driver_type='property'):
    # Detect violations from incoming ELD data
    violations = detect_hos_violations(eld_data_list)

    # Check if any violation exists
    violation_exists = any(
        any(violations[i].values())
        for i in range(len(violations))
    )

    # Provide a recommended schedule to avoid violations
    recommended_schedule = calculate_schedule_with_sleeper_berth(pickup_time_str, dropoff_time_str, driver_type)

    return {
        'violation_exists': violation_exists,
        'violations': violations,
        'recommended_schedule': recommended_schedule,
    }