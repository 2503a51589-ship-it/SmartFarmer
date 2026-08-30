import math
from datetime import datetime, timedelta

class SmartQueueEngine:
    """
    SIH26032 Innovation: Smart Queue Prediction & Recommendation Engine
    Analyzes queue congestion, calculates waiting times, and recommends optimal procurement centers.
    """
    
    @staticmethod
    def calculate_estimated_wait_time(people_ahead, counters=2, avg_processing_time=15):
        if people_ahead <= 0:
            return 0
        effective_counters = max(1, int(counters if counters else 1))
        effective_avg_time = max(5, int(avg_processing_time if avg_processing_time else 15))
        batches_ahead = math.ceil(people_ahead / effective_counters)
        return int(batches_ahead * effective_avg_time)

    @staticmethod
    def get_congestion_level(wait_time_minutes, people_ahead=0, counters=2):
        if wait_time_minutes <= 20:
            return {
                'level': 'LOW CONGESTION',
                'class': 'success',
                'bg_class': 'bg-success',
                'text_class': 'text-success',
                'badge_color': '#198754',
                'icon': 'bi-check-circle-fill',
                'description': 'Smooth flow. Minimal waiting time expected.'
            }
        elif wait_time_minutes <= 45:
            return {
                'level': 'MEDIUM CONGESTION',
                'class': 'warning',
                'bg_class': 'bg-warning',
                'text_class': 'text-warning',
                'badge_color': '#ffc107',
                'icon': 'bi-exclamation-circle-fill',
                'description': 'Moderate farmer turnout. Expected processing time is normal.'
            }
        else:
            return {
                'level': 'HIGH CONGESTION',
                'class': 'danger',
                'bg_class': 'bg-danger',
                'text_class': 'text-danger',
                'badge_color': '#dc3545',
                'icon': 'bi-exclamation-triangle-fill',
                'description': 'Heavy rush today. Expect longer wait times or consider alternate centers.'
            }

    @staticmethod
    def calculate_expected_completion_time(wait_time_minutes, base_time=None):
        if base_time is None:
            base_time = datetime.now()
        completion_dt = base_time + timedelta(minutes=wait_time_minutes)
        return completion_dt.strftime('%I:%M %p')

    @classmethod
    def analyze_center_queue(cls, center_id, center_name, active_queue_list, total_counters=3, avg_proc_time=15):
        waiting_count = sum(1 for item in active_queue_list if item.get('status') in ['Waiting', 'Calling', 'In-Process'])
        in_process_count = sum(1 for item in active_queue_list if item.get('status') in ['In-Process', 'Calling'])
        completed_count = sum(1 for item in active_queue_list if item.get('status') == 'Completed')
        
        wait_time = cls.calculate_estimated_wait_time(waiting_count, total_counters, avg_proc_time)
        congestion = cls.get_congestion_level(wait_time, waiting_count, total_counters)
        
        return {
            'center_id': center_id,
            'center_name': center_name,
            'total_counters': total_counters,
            'avg_processing_time': avg_proc_time,
            'waiting_farmers': waiting_count,
            'in_process_farmers': in_process_count,
            'completed_farmers': completed_count,
            'total_today': len(active_queue_list),
            'estimated_wait_time': wait_time,
            'expected_completion_time': cls.calculate_expected_completion_time(wait_time),
            'congestion': congestion
        }

    @classmethod
    def get_smart_recommendation(cls, centers_analysis, current_center_id=None):
        if not centers_analysis:
            return None
        
        sorted_centers = sorted(
            centers_analysis,
            key=lambda c: (c['estimated_wait_time'], c['waiting_farmers'])
        )
        
        best_center = sorted_centers[0]
        is_current_best = (current_center_id is not None and best_center['center_id'] == current_center_id)
        
        worst_wait = max(c['estimated_wait_time'] for c in centers_analysis)
        time_saved = max(0, worst_wait - best_center['estimated_wait_time'])
        
        reason = f"This center currently has the shortest queue ({best_center['waiting_farmers']} farmers) with {best_center['total_counters']} active counters, minimizing your waiting time to approx {best_center['estimated_wait_time']} minutes."
        if time_saved > 10:
            reason += f" (Saves ~{time_saved} minutes compared to busiest centers)."
            
        return {
            'recommended_center': best_center,
            'center_name': best_center['center_name'],
            'center_id': best_center['center_id'],
            'current_queue': best_center['waiting_farmers'],
            'estimated_waiting_time': best_center['estimated_wait_time'],
            'congestion_level': best_center['congestion']['level'],
            'congestion_class': best_center['congestion']['class'],
            'congestion_bg': best_center['congestion']['bg_class'],
            'reason': reason,
            'is_current_best': is_current_best,
            'all_centers': sorted_centers
        }

    @classmethod
    def build_visual_queue(cls, queue_records, current_user_token=None):
        visual_list = []
        people_ahead = 0
        found_current = False
        
        for idx, item in enumerate(queue_records):
            token = item.get('token_number')
            status = item.get('status')
            is_current = bool(current_user_token and str(token).strip().upper() == str(current_user_token).strip().upper())
            
            if is_current:
                found_current = True
            elif not found_current and status in ['Waiting', 'Calling', 'In-Process']:
                people_ahead += 1
                
            visual_list.append({
                'token': token,
                'farmer_name': item.get('farmer_name', 'Farmer'),
                'crop_name': item.get('crop_name', 'Crop'),
                'crop_quantity': item.get('crop_quantity', 0),
                'status': status,
                'counter': item.get('counter_assigned', 1),
                'is_current_farmer': is_current,
                'position_index': idx + 1
            })
            
        return {
            'visual_items': visual_list,
            'people_ahead': people_ahead,
            'estimated_wait_mins': cls.calculate_estimated_wait_time(people_ahead) if found_current else 0
        }
