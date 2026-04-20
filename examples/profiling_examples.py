"""
PyInstrument Profiling Examples
Demonstrates different ways to profile code for performance optimization
"""
import requests
import time
from typing import List, Dict, Any
from pyinstrument import Profiler
from app.utils.profiling import (
    profile_function,
    ProfileContext,
    start_profile,
    stop_profile,
    profile_api_endpoint
)


# =============================================================================
# Example 1: Function Decorator (Recommended for permanent profiling)
# =============================================================================

@profile_function(name="process_videos", save_html=True, min_duration=0.5)
def process_multiple_videos(video_ids: List[str]):
    """
    Profile entire function execution
    Automatically saves HTML if execution > 0.5s
    """
    results = []
    for video_id in video_ids:
        result = process_single_video(video_id)
        results.append(result)
    return results


def process_single_video(video_id: str):
    """Simulate video processing"""
    time.sleep(0.1)  # Simulate work
    return {"id": video_id, "status": "done"}


# =============================================================================
# Example 2: Context Manager (Good for profiling specific code blocks)
# =============================================================================

def fetch_and_process_data(api_url: str):
    """
    Profile only the expensive part
    """
    # Not profiled
    headers = {"Authorization": "Bearer token"}
    
    # Profile just the API call
    with ProfileContext("api_fetch", save_html=True) as p:
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()
    
    print(f"API call took: {p.duration:.3f}s")
    
    # Not profiled
    return process_data(data)


def process_data(data):
    """Simulate data processing"""
    return len(data)


# =============================================================================
# Example 3: Manual Profiler (Maximum control)
# =============================================================================

def complex_workflow_with_multiple_steps():
    """
    Profile different parts separately
    """
    # Start profiling
    profiler = start_profile("full_workflow")
    
    # Step 1: Load data
    data = load_large_dataset()
    
    # Step 2: Transform
    transformed = transform_data(data)
    
    # Step 3: Save
    save_results(transformed)
    
    # Stop and save profile
    stop_profile(profiler, "full_workflow", save_html=True)


def load_large_dataset():
    time.sleep(0.5)
    return [{"id": i} for i in range(1000)]


def transform_data(data):
    time.sleep(0.3)
    return [{"id": d["id"], "value": d["id"] * 2} for d in data]


def save_results(data):
    time.sleep(0.2)
    return len(data)


# =============================================================================
# Example 4: Profiling API Calls in Task Browser
# =============================================================================

def fetch_tasks_with_profiling(api_base_url: str, api_headers: dict, page: int = 1):
    """
    Example: Profile API call in Task Browser
    """
    # Enable profiling via environment or config
    enable_profiling = True  # Or os.getenv("ENABLE_PROFILING") == "true"
    
    if enable_profiling:
        profiler = Profiler()
        profiler.start()
    
    try:
        # Make API call
        response = requests.get(
            f"{api_base_url}/api/v1/tasks",
            headers=api_headers,
            params={"page": page, "page_size": 50},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if enable_profiling:
            profiler.stop()
            duration = profiler.last_session.duration
            
            if duration > 0.1:  # Only log if > 100ms
                print(f"⏱️  fetch_tasks took {duration:.3f}s")
                print(profiler.output_text(unicode=True, color=True))
                
                # Optionally save HTML
                # with open('fetch_tasks_profile.html', 'w') as f:
                #     f.write(profiler.output_html())
        
        return result
    
    except Exception as e:
        if enable_profiling:
            profiler.stop()
        raise


# =============================================================================
# Example 5: Conditional Profiling (Profile only specific conditions)
# =============================================================================

def process_task(task_id: str, enable_profiling: bool = False):
    """
    Only profile when explicitly requested
    Useful for production debugging
    """
    if enable_profiling:
        with ProfileContext(f"task_{task_id}", save_html=True) as p:
            result = _do_process_task(task_id)
        print(f"Task {task_id} took {p.duration:.3f}s")
        return result
    else:
        # No profiling overhead
        return _do_process_task(task_id)


def _do_process_task(task_id: str):
    """Actual task processing"""
    time.sleep(0.5)
    return {"task_id": task_id, "status": "completed"}


# =============================================================================
# Example 6: Profiling Multiple Functions to Compare
# =============================================================================

@profile_function(name="method_a", print_results=False)
def method_a(data: List[int]) -> int:
    """Slow method"""
    total = 0
    for i in data:
        total += i ** 2
    return total


@profile_function(name="method_b", print_results=False)
def method_b(data: List[int]) -> int:
    """Fast method"""
    return sum(i ** 2 for i in data)


def compare_methods():
    """Compare performance of two methods"""
    data = list(range(100000))
    
    result_a = method_a(data)
    result_b = method_b(data)
    
    print(f"Results match: {result_a == result_b}")


# =============================================================================
# Example 7: Profiling Async Functions (FastAPI endpoints)
# =============================================================================

# from fastapi import APIRouter
# router = APIRouter()
# 
# @router.post("/api/v1/videos")
# @profile_api_endpoint(name="create_video_api", save_html=True)
# async def create_video_endpoint(params: dict):
#     """
#     Profile async API endpoint
#     Automatically handles async functions
#     """
#     # Simulate async work
#     await asyncio.sleep(1.0)
#     
#     result = {
#         "task_id": "abc123",
#         "status": "created"
#     }
#     
#     return result


# =============================================================================
# Example 8: Profiling with Custom Thresholds
# =============================================================================

@profile_function(name="fast_op", min_duration=0.01)  # Only log if > 10ms
def fast_operation():
    """Quick operation - higher threshold"""
    time.sleep(0.005)
    return "done"


@profile_function(name="slow_op", min_duration=5.0)  # Only log if > 5s
def slow_operation():
    """Slow operation - higher threshold"""
    time.sleep(2.0)
    return "done"


# =============================================================================
# Example 9: Nested Profiling (Profile sub-operations)
# =============================================================================

@profile_function(name="parent_operation", save_html=True)
def parent_operation():
    """
    Outer profile captures everything
    Inner profiles show sub-operation details
    """
    # This will be profiled as part of parent
    with ProfileContext("child_operation_1") as p1:
        time.sleep(0.2)
    
    with ProfileContext("child_operation_2") as p2:
        time.sleep(0.3)
    
    print(f"Child 1: {p1.duration:.3f}s")
    print(f"Child 2: {p2.duration:.3f}s")
    
    return "done"


# =============================================================================
# Example 10: Real-World Video Processing Example
# =============================================================================

@profile_function(name="full_video_pipeline", save_html=True, min_duration=1.0)
def create_video_with_profiling(video_subject: str):
    """
    Complete video creation pipeline with profiling
    Shows where time is spent in each step
    """
    # Step 1: Generate script
    with ProfileContext("generate_script") as p1:
        script = generate_script_stub(video_subject)
    print(f"Script generation: {p1.duration:.3f}s")
    
    # Step 2: Generate keywords
    with ProfileContext("generate_keywords") as p2:
        keywords = generate_keywords_stub(script)
    print(f"Keyword generation: {p2.duration:.3f}s")
    
    # Step 3: Download videos
    with ProfileContext("download_videos") as p3:
        video_files = download_videos_stub(keywords)
    print(f"Video download: {p3.duration:.3f}s")
    
    # Step 4: Combine videos
    with ProfileContext("combine_videos") as p4:
        final_video = combine_videos_stub(video_files, script)
    print(f"Video combination: {p4.duration:.3f}s")
    
    return final_video


def generate_script_stub(subject: str) -> str:
    time.sleep(0.5)
    return f"Script about {subject}"


def generate_keywords_stub(script: str) -> List[str]:
    time.sleep(0.3)
    return ["keyword1", "keyword2", "keyword3"]


def download_videos_stub(keywords: List[str]) -> List[str]:
    time.sleep(1.0)
    return [f"video_{i}.mp4" for i in range(len(keywords))]


def combine_videos_stub(files: List[str], script: str) -> str:
    time.sleep(2.0)
    return "final_video.mp4"


# =============================================================================
# Main: Run Examples
# =============================================================================

if __name__ == "__main__":
    import os
    
    # Enable profiling
    os.environ["ENABLE_PROFILING"] = "true"
    os.environ["PROFILE_MIN_DURATION"] = "0.1"
    
    print("=" * 60)
    print("Running Profiling Examples")
    print("=" * 60)
    
    # Example 1: Function decorator
    print("\n1. Function Decorator:")
    process_multiple_videos(["v1", "v2", "v3"])
    
    # Example 3: Manual profiler
    print("\n3. Manual Profiler:")
    complex_workflow_with_multiple_steps()
    
    # Example 5: Conditional profiling
    print("\n5. Conditional Profiling:")
    process_task("task_123", enable_profiling=True)
    
    # Example 9: Nested profiling
    print("\n9. Nested Profiling:")
    parent_operation()
    
    # Example 10: Real-world video pipeline
    print("\n10. Video Pipeline:")
    create_video_with_profiling("AI and Healthcare")
    
    print("\n" + "=" * 60)
    print("Check /MoneyPrinterTurbo/storage/profiles/ for HTML reports!")
    print("=" * 60)
