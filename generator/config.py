"""
Configuration for Synthetic Vibration Data Generator

This file defines all parameters for simulating motor test bench vibration data.
"""

import uuid
from dataclasses import dataclass
from typing import List, Tuple
from datetime import datetime


@dataclass
class SensorConfig:
    """Accelerometer sensor configuration"""
    sampling_rate_hz: float = 25600.0  # 25.6 kHz as per data contract
    axes: List[str] = None  # ['acc_x', 'acc_y', 'acc_z']
    
    # Physical limits (m/s²)
    max_acceleration: float = 200.0
    min_acceleration: float = -200.0
    
    # Noise characteristics
    baseline_noise_std: float = 0.5  # Standard deviation of background noise (m/s²)
    
    def __post_init__(self):
        if self.axes is None:
            self.axes = ['acc_x', 'acc_y', 'acc_z']
    
    @property
    def sample_interval(self) -> float:
        """Time between samples in seconds"""
        return 1.0 / self.sampling_rate_hz


@dataclass
class RPMConfig:
    """RPM sensor configuration"""
    sampling_rate_hz: float = 50.0  # Much lower rate than accelerometers
    max_rpm: float = 12000.0
    min_rpm: float = 0.0


@dataclass
class PhaseConfig:
    """Test phase configuration"""
    name: str  # 'idle', 'run-up', 'steady', 'run-down'
    duration_sec: float
    start_rpm: float
    end_rpm: float
    
    @property
    def rpm_rate(self) -> float:
        """RPM change per second"""
        if self.duration_sec == 0:
            return 0.0
        return (self.end_rpm - self.start_rpm) / self.duration_sec


@dataclass
class SessionConfig:
    """Complete test session configuration"""
    
    # Identity
    test_id: str = None
    bench_id: str = "BENCH-01"
    motor_variant: str = "MTR-V3-2023"
    firmware_version: str = "FW-2.1.5"
    session_start: datetime = None
    
    # Phases (default: realistic test profile)
    phases: List[PhaseConfig] = None
    
    # Sensors
    sensor: SensorConfig = None
    rpm_sensor: RPMConfig = None
    
    def __post_init__(self):
        # Generate unique test ID
        if self.test_id is None:
            self.test_id = str(uuid.uuid4())[:8]
        
        # Set session start time
        if self.session_start is None:
            self.session_start = datetime.now()
        
        # Initialize sensors
        if self.sensor is None:
            self.sensor = SensorConfig()
        if self.rpm_sensor is None:
            self.rpm_sensor = RPMConfig()
        
        # Default phase profile if not specified
        if self.phases is None:
            self.phases = self._default_phases()
    
    def _default_phases(self) -> List[PhaseConfig]:
        """
        Creates a realistic test profile:
        1. Idle: 10 seconds at 0 RPM
        2. Run-up: 30 seconds, 0 → 3000 RPM
        3. Steady: 120 seconds at 3000 RPM
        4. Run-down: 30 seconds, 3000 → 0 RPM
        
        Total duration: 190 seconds (~3 minutes)
        """
        return [
            PhaseConfig(name='idle', duration_sec=10, start_rpm=0, end_rpm=0),
            PhaseConfig(name='run-up', duration_sec=30, start_rpm=0, end_rpm=3000),
            PhaseConfig(name='steady', duration_sec=120, start_rpm=3000, end_rpm=3000),
            PhaseConfig(name='run-down', duration_sec=30, start_rpm=3000, end_rpm=0),
        ]
    
    @property
    def total_duration(self) -> float:
        """Total session duration in seconds"""
        return sum(phase.duration_sec for phase in self.phases)
    
    @property
    def total_samples(self) -> int:
        """Total number of accelerometer samples"""
        return int(self.total_duration * self.sensor.sampling_rate_hz)


@dataclass
class VibrationPhysics:
    """
    Physical model parameters for realistic vibration
    
    Motor vibrations have multiple frequency components:
    1. Rotational frequency (1× RPM)
    2. Harmonics (2×, 3×, 4× RPM)
    3. Bearing frequencies (depends on geometry)
    4. Broadband noise
    """
    
    # Harmonic amplitudes (decreasing with order)
    # These are multipliers on base vibration amplitude
    harmonic_orders: List[int] = None
    harmonic_amplitudes: List[float] = None
    
    # Base vibration amplitude scales with RPM
    base_amplitude_per_1000rpm: float = 2.0  # m/s² per 1000 RPM
    
    # Bearing fault frequencies (as fraction of RPM)
    # These are typical for ball bearings
    bearing_bpfo: float = 3.5  # Ball Pass Frequency Outer race
    bearing_bpfi: float = 5.4  # Ball Pass Frequency Inner race
    bearing_bsf: float = 2.3   # Ball Spin Frequency
    bearing_ftf: float = 0.4   # Fundamental Train Frequency
    
    # Modulation parameters
    amplitude_modulation_freq: float = 0.5  # Hz (slow variation)
    amplitude_modulation_depth: float = 0.1  # 10% modulation
    
    def __post_init__(self):
        if self.harmonic_orders is None:
            self.harmonic_orders = [1, 2, 3, 4, 5]  # 1× to 5× RPM
        if self.harmonic_amplitudes is None:
            # Amplitudes decrease with harmonic order
            self.harmonic_amplitudes = [1.0, 0.4, 0.2, 0.1, 0.05]


@dataclass
class AnomalyConfig:
    """Configuration for injecting anomalies"""
    
    # Enable/disable anomaly types
    inject_spike: bool = False
    inject_dropout: bool = False
    inject_stuck_sensor: bool = False
    inject_elevated_rms: bool = False
    
    # Spike parameters (bearing-like fault)
    spike_start_time: float = 60.0  # seconds into session
    spike_duration: float = 0.1  # seconds
    spike_amplitude: float = 50.0  # m/s²
    
    # Dropout parameters (communication failure)
    dropout_start_time: float = 100.0
    dropout_duration: float = 0.5  # seconds
    
    # Stuck sensor parameters (sensor failure)
    stuck_start_time: float = 150.0
    stuck_duration: float = 2.0  # seconds
    stuck_value: float = 5.0  # m/s² (arbitrary constant)
    
    # Elevated RMS (degraded bearing)
    elevated_rms_start_time: float = 80.0
    elevated_rms_duration: float = 20.0  # seconds
    elevated_rms_multiplier: float = 3.0  # 3× normal amplitude


# Default configurations for quick testing
DEFAULT_SESSION = SessionConfig()
DEFAULT_PHYSICS = VibrationPhysics()
DEFAULT_ANOMALY = AnomalyConfig()


# Variant configurations for different motor types
MOTOR_VARIANTS = {
    'MTR-V3-2023': {
        'max_rpm': 6000,
        'base_vibration': 2.0,
        'description': 'Standard 3kW motor'
    },
    'MTR-V5-2024': {
        'max_rpm': 9000,
        'base_vibration': 1.5,
        'description': 'High-speed 5kW motor'
    },
    'MTR-HEAVY-2022': {
        'max_rpm': 3000,
        'base_vibration': 4.0,
        'description': 'Industrial heavy-duty motor'
    }
}


if __name__ == '__main__':
    # Quick test of configuration
    config = SessionConfig()
    print(f"Test ID: {config.test_id}")
    print(f"Total duration: {config.total_duration} seconds")
    print(f"Total samples: {config.total_samples:,}")
    print(f"Sample interval: {config.sensor.sample_interval*1e6:.2f} microseconds")
    print(f"\nPhases:")
    for phase in config.phases:
        print(f"  {phase.name:10s}: {phase.duration_sec:6.1f}s, "
              f"{phase.start_rpm:6.0f} → {phase.end_rpm:6.0f} RPM")
