import numpy as np
import random
import math
from collections import defaultdict
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon
import pyqtgraph.opengl as gl
import json
import os
from datetime import datetime

particle_data = {
    "ELECTRON": ("e-", 0.000511, -1, 1e30, 0.5, (1, 0, 0, 1)),
    "POSITRON": ("e+", 0.000511, 1, 1e30, 0.5, (0, 1, 0, 1)),
    "MUON": ("μ-", 0.105, -1, 2.2e-6, 0.5, (0, 0, 1, 1)),
    "ANTIMUON": ("μ+", 0.105, 1, 2.2e-6, 0.5, (1, 1, 0, 1)),
    "PROTON": ("p+", 0.938, 1, 1e30, 0.5, (1, 0, 1, 1)),
    "ANTIPROTON": ("p-", 0.938, -1, 1e30, 0.5, (0, 1, 1, 1)),
    "PHOTON": ("γ", 0, 0, 1e30, 1, (1, 1, 1, 1)),
    "PION_PLUS": ("π+", 0.140, 1, 2.6e-8, 0, (1, 0.5, 0, 1)),
    "PION_MINUS": ("π-", 0.140, -1, 2.6e-8, 0, (1, 0.3, 0, 1)),
    "HIGGS": ("H", 125.0, 0, 1.6e-22, 0, (0.5, 0, 0.5, 1)),
    "NEUTRON": ("n", 0.940, 0, 880, 0.5, (0.7, 0.7, 0.7, 1)),
    "GLUON": ("g", 0, 0, 1e30, 1, (0.9, 0.6, 0.1, 1))
}

simulator_state = {
    'particles': [],
    'collision_events': [],
    'entangled_pairs': [],
    'time': 0.0,
    'event_counter': 0,
    'particle_counter': 0,
    'collision_distance': 0.1,
    'annihilation_probability': 0.3,
    'particle_creation_probability': 0.2,
    'beam_energy': 7.0,
    'num_particles': 30,
    'beam1_particles': ["PROTON", "ANTIPROTON"],
    'beam2_particles': ["PROTON", "ANTIPROTON"],
    'beam1_energy': 7.0,
    'beam2_energy': 7.0,
    'beam_spread': 0.5,
    'momentum_spread': 0.1
}

particles = []
collision_events = []
entangled_pairs = []
particle_items = []
trajectory_items = []
collision_items = []
info_items = []
is_running = False
simulation_speed = 5
timer = None
gl_widget = None
stats_label = None
beam1_button = None
beam2_button = None
beam1_label = None
beam2_label = None
beam1_energy_spin = None
beam2_energy_spin = None
beam_spread_spin = None
momentum_spread_spin = None
start_btn = None
pause_btn = None
reset_btn = None
speed_slider = None
speed_label = None
collision_dist_spin = None
annihilation_prob_spin = None
creation_prob_spin = None
particle_count_spin = None
show_trajectories = None
show_collision_rings = None
show_particle_info = None

app = QApplication(sys.argv)
app.setStyle('Windows')
font = QFont("Arial", 9)
app.setFont(font)
window = QMainWindow()
window.setWindowTitle("Particle Realm Simulator - 可配置对撞")
window.showFullScreen()
central_widget = QWidget()
window.setCentralWidget(central_widget)
main_layout = QHBoxLayout(central_widget)
control_panel = QWidget()
control_panel.setMaximumWidth(350)
control_layout = QVBoxLayout(control_panel)

beam_group = QGroupBox("束流配置")
beam_layout = QVBoxLayout(beam_group)

beam1_layout = QHBoxLayout()
beam1_button = QPushButton("束流1粒子")
beam1_label = QLabel("质子/反质子")
beam1_layout.addWidget(QLabel("束流1:"))
beam1_layout.addWidget(beam1_button)
beam1_layout.addWidget(beam1_label)
beam1_layout.addStretch()

beam1_energy_spin = QDoubleSpinBox()
beam1_energy_spin.setRange(0.1, 100.0)
beam1_energy_spin.setValue(7.0)
beam1_energy_spin.setSingleStep(0.1)
beam1_layout.addWidget(QLabel("能量:"))
beam1_layout.addWidget(beam1_energy_spin)

beam_layout.addLayout(beam1_layout)

beam2_layout = QHBoxLayout()
beam2_button = QPushButton("束流2粒子")
beam2_label = QLabel("质子/反质子")
beam2_layout.addWidget(QLabel("束流2:"))
beam2_layout.addWidget(beam2_button)
beam2_layout.addWidget(beam2_label)
beam2_layout.addStretch()

beam2_energy_spin = QDoubleSpinBox()
beam2_energy_spin.setRange(0.1, 100.0)
beam2_energy_spin.setValue(7.0)
beam2_energy_spin.setSingleStep(0.1)
beam2_layout.addWidget(QLabel("能量:"))
beam2_layout.addWidget(beam2_energy_spin)

beam_layout.addLayout(beam2_layout)

beam_params_layout = QHBoxLayout()
beam_spread_spin = QDoubleSpinBox()
beam_spread_spin.setRange(0.01, 2.0)
beam_spread_spin.setValue(0.5)
beam_spread_spin.setSingleStep(0.05)
beam_params_layout.addWidget(QLabel("束流散布:"))
beam_params_layout.addWidget(beam_spread_spin)

momentum_spread_spin = QDoubleSpinBox()
momentum_spread_spin.setRange(0.01, 1.0)
momentum_spread_spin.setValue(0.1)
momentum_spread_spin.setSingleStep(0.01)
beam_params_layout.addWidget(QLabel("动量散布:"))
beam_params_layout.addWidget(momentum_spread_spin)

beam_layout.addLayout(beam_params_layout)

sim_group = QGroupBox("模拟控制")
sim_layout = QVBoxLayout(sim_group)
start_btn = QPushButton("▶ 开始模拟")
pause_btn = QPushButton("⏸ 暂停")
reset_btn = QPushButton("🔄 重置")
speed_slider = QSlider(Qt.Horizontal)
speed_slider.setRange(1, 20)
speed_slider.setValue(5)
speed_label = QLabel("速度: 5x")
sim_layout.addWidget(start_btn)
sim_layout.addWidget(pause_btn)
sim_layout.addWidget(reset_btn)
sim_layout.addWidget(QLabel("模拟速度:"))
sim_layout.addWidget(speed_slider)
sim_layout.addWidget(speed_label)

param_group = QGroupBox("碰撞参数")
param_layout = QVBoxLayout(param_group)
collision_dist_spin = QDoubleSpinBox()
collision_dist_spin.setRange(0.01, 1.0)
collision_dist_spin.setValue(0.1)
collision_dist_spin.setSingleStep(0.01)
annihilation_prob_spin = QDoubleSpinBox()
annihilation_prob_spin.setRange(0.0, 1.0)
annihilation_prob_spin.setValue(0.3)
annihilation_prob_spin.setSingleStep(0.05)
creation_prob_spin = QDoubleSpinBox()
creation_prob_spin.setRange(0.0, 1.0)
creation_prob_spin.setValue(0.2)
creation_prob_spin.setSingleStep(0.05)
particle_count_spin = QSpinBox()
particle_count_spin.setRange(10, 200)
particle_count_spin.setValue(30)

param_layout.addWidget(QLabel("碰撞距离:"))
param_layout.addWidget(collision_dist_spin)
param_layout.addWidget(QLabel("湮灭概率:"))
param_layout.addWidget(annihilation_prob_spin)
param_layout.addWidget(QLabel("粒子产生概率:"))
param_layout.addWidget(creation_prob_spin)
param_layout.addWidget(QLabel("粒子数量:"))
param_layout.addWidget(particle_count_spin)

display_group = QGroupBox("显示选项")
display_layout = QVBoxLayout(display_group)
show_trajectories = QCheckBox("显示粒子轨迹")
show_trajectories.setChecked(True)
show_collision_rings = QCheckBox("显示碰撞效果")
show_collision_rings.setChecked(True)
show_particle_info = QCheckBox("显示粒子信息")
show_particle_info.setChecked(True)
display_layout.addWidget(show_trajectories)
display_layout.addWidget(show_collision_rings)
display_layout.addWidget(show_particle_info)

stats_group = QGroupBox("实时统计")
stats_layout = QVBoxLayout(stats_group)
stats_label = QLabel("统计信息将显示在这里...")
stats_label.setWordWrap(True)
stats_layout.addWidget(stats_label)

control_layout.addWidget(beam_group)
control_layout.addWidget(sim_group)
control_layout.addWidget(param_group)
control_layout.addWidget(display_group)
control_layout.addWidget(stats_group)
control_layout.addStretch()

gl_widget = gl.GLViewWidget()
gl_widget.setCameraPosition(distance=25, elevation=20, azimuth=45)
main_layout.addWidget(control_panel)
main_layout.addWidget(gl_widget)

detector_radius = 3.0
detector_length = 20.0
u = np.linspace(0, 2 * np.pi, 50)
z = np.linspace(-detector_length / 2, detector_length / 2, 2)
U, Z = np.meshgrid(u, z)
X = detector_radius * np.cos(U)
Y = detector_radius * np.sin(U)
detector_mesh = gl.GLMeshItem(
    vertexes=np.dstack([X, Y, Z]),
    smooth=True,
    color=(0.2, 0.2, 0.2, 0.2),
    drawEdges=True,
    edgeColor=(0.4, 0.4, 0.4, 0.6)
)
gl_widget.addItem(detector_mesh)

axis_length = 5.0
x_axis = gl.GLLinePlotItem(
    pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
    color=(1, 0, 0, 1), width=3
)
gl_widget.addItem(x_axis)
y_axis = gl.GLLinePlotItem(
    pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
    color=(0, 1, 0, 1), width=3
)
gl_widget.addItem(y_axis)
z_axis = gl.GLLinePlotItem(
    pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
    color=(0, 0, 1, 1), width=3
)
gl_widget.addItem(z_axis)

timer = QTimer()

simulator_state['particles'] = []
simulator_state['collision_events'] = []
simulator_state['entangled_pairs'] = []
simulator_state['time'] = 0.0
simulator_state['event_counter'] = 0
simulator_state['particle_counter'] = 0

beam1_types = simulator_state['beam1_particles']
beam2_types = simulator_state['beam2_particles']

if not beam1_types:
    beam1_types = ["PROTON"]
if not beam2_types:
    beam2_types = ["PROTON"]

for i in range(simulator_state['num_particles']):
    p_type1 = random.choice(beam1_types)
    momentum1 = np.array([
        simulator_state['beam1_energy'],
        random.gauss(0, simulator_state['momentum_spread']),
        random.gauss(0, simulator_state['momentum_spread'])
    ])
    position1 = np.array([
        -8,
        random.gauss(0, simulator_state['beam_spread']),
        random.gauss(0, simulator_state['beam_spread'])
    ])

    particle1 = {
        'particle_id': simulator_state['particle_counter'],
        'particle_type': p_type1,
        'position': position1,
        'momentum': momentum1,
        'mass': particle_data[p_type1][1],
        'charge': particle_data[p_type1][2],
        'lifetime': particle_data[p_type1][3],
        'spin': random.choice(["UP", "DOWN", "LEFT", "RIGHT"]),
        'trajectory': [position1.copy()],
        'creation_time': 0.0,
        'velocity_history': []
    }
    particle1['energy'] = math.sqrt(np.linalg.norm(momentum1) ** 2 + particle1['mass'] ** 2)
    simulator_state['particle_counter'] += 1
    simulator_state['particles'].append(particle1)

    p_type2 = random.choice(beam2_types)
    momentum2 = np.array([
        -simulator_state['beam2_energy'],
        random.gauss(0, simulator_state['momentum_spread']),
        random.gauss(0, simulator_state['momentum_spread'])
    ])
    position2 = np.array([
        8,
        random.gauss(0, simulator_state['beam_spread']),
        random.gauss(0, simulator_state['beam_spread'])
    ])

    particle2 = {
        'particle_id': simulator_state['particle_counter'],
        'particle_type': p_type2,
        'position': position2,
        'momentum': momentum2,
        'mass': particle_data[p_type2][1],
        'charge': particle_data[p_type2][2],
        'lifetime': particle_data[p_type2][3],
        'spin': random.choice(["UP", "DOWN", "LEFT", "RIGHT"]),
        'trajectory': [position2.copy()],
        'creation_time': 0.0,
        'velocity_history': []
    }
    particle2['energy'] = math.sqrt(np.linalg.norm(momentum2) ** 2 + particle2['mass'] ** 2)
    simulator_state['particle_counter'] += 1
    simulator_state['particles'].append(particle2)

def save_collider_config():
    """保存对撞机配置到.lhc文件"""
    config = {
        'beam1_particles': simulator_state['beam1_particles'],
        'beam2_particles': simulator_state['beam2_particles'],
        'beam1_energy': simulator_state['beam1_energy'],
        'beam2_energy': simulator_state['beam2_energy'],
        'beam_spread': simulator_state['beam_spread'],
        'momentum_spread': simulator_state['momentum_spread'],
        'collision_distance': simulator_state['collision_distance'],
        'annihilation_probability': simulator_state['annihilation_probability'],
        'particle_creation_probability': simulator_state['particle_creation_probability'],
        'num_particles': simulator_state['num_particles'],
        'simulation_speed': simulation_speed,
        'show_trajectories': show_trajectories.isChecked(),
        'show_collision_rings': show_collision_rings.isChecked(),
        'show_particle_info': show_particle_info.isChecked(),
        'timestamp': datetime.now().isoformat(),
        'simulator_type': 'particle_collider',
        'version': '1.0',
        'description': '大型强子对撞机模拟器配置文件'
    }

    file_path, _ = QFileDialog.getSaveFileName(
        window,
        "保存对撞机配置",
        f"LHC_Simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.lhc",
        "LHC Configuration Files (*.lhc);;All Files (*)"
    )

    if file_path:
        # 确保文件后缀是.lhc
        if not file_path.lower().endswith('.lhc'):
            file_path += '.lhc'

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            QMessageBox.information(window, "成功", f"对撞机配置已保存到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(window, "错误", f"保存配置失败: {str(e)}")


def load_collider_config():
    """从.lhc文件加载对撞机配置"""
    if is_running:
        QMessageBox.warning(window, "警告", "请先停止模拟再加载配置")
        return

    file_path, _ = QFileDialog.getOpenFileName(
        window,
        "加载对撞机配置",
        "",
        "LHC Configuration Files (*.lhc);;JSON Files (*.json);;All Files (*)"
    )

    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 验证配置文件类型和版本
            if config.get('simulator_type') != 'particle_collider':
                QMessageBox.warning(
                    window,
                    "文件类型错误",
                    "这不是有效的对撞机配置文件\n请选择.lhc格式的文件"
                )
                return

            # 检查版本兼容性
            file_version = config.get('version', '1.0')
            if file_version != '1.0':
                reply = QMessageBox.question(
                    window,
                    "版本警告",
                    f"此配置文件版本 ({file_version}) 可能与当前版本 (1.0) 不兼容\n是否继续加载?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # 更新界面控件
            simulator_state['beam1_particles'] = config.get('beam1_particles', ["PROTON", "ANTIPROTON"])
            simulator_state['beam2_particles'] = config.get('beam2_particles', ["PROTON", "ANTIPROTON"])

            # 更新标签显示
            labels1 = [particle_data[p][0] for p in simulator_state['beam1_particles']]
            labels2 = [particle_data[p][0] for p in simulator_state['beam2_particles']]
            beam1_label.setText("/".join(labels1) if len(labels1) <= 3 else f"{len(labels1)}种粒子")
            beam2_label.setText("/".join(labels2) if len(labels2) <= 3 else f"{len(labels2)}种粒子")

            # 更新数值控件
            beam1_energy_spin.setValue(config.get('beam1_energy', 7.0))
            beam2_energy_spin.setValue(config.get('beam2_energy', 7.0))
            beam_spread_spin.setValue(config.get('beam_spread', 0.5))
            momentum_spread_spin.setValue(config.get('momentum_spread', 0.1))
            collision_dist_spin.setValue(config.get('collision_distance', 0.1))
            annihilation_prob_spin.setValue(config.get('annihilation_probability', 0.3))
            creation_prob_spin.setValue(config.get('particle_creation_probability', 0.2))
            particle_count_spin.setValue(config.get('num_particles', 30))
            speed_slider.setValue(config.get('simulation_speed', 5))

            # 更新显示选项
            show_trajectories.setChecked(config.get('show_trajectories', True))
            show_collision_rings.setChecked(config.get('show_collision_rings', True))
            show_particle_info.setChecked(config.get('show_particle_info', True))

            # 更新状态变量
            update_physics_params()
            update_beam_params()
            update_particle_count()
            update_speed(speed_slider.value())

            # 显示文件信息
            file_info = f"配置文件: {os.path.basename(file_path)}"
            if 'description' in config:
                file_info += f"\n描述: {config['description']}"
            if 'timestamp' in config:
                file_info += f"\n创建时间: {config['timestamp'][:19]}"

            QMessageBox.information(window, "加载成功", file_info)

        except json.JSONDecodeError:
            QMessageBox.critical(window, "文件错误", "文件格式错误，不是有效的JSON文件")
        except Exception as e:
            QMessageBox.critical(window, "错误", f"加载配置失败: {str(e)}")
# 在控制面板添加导入导出按钮
def add_collider_import_export_buttons():
    """为对撞机添加导入导出按钮"""
    import_export_group = QGroupBox("配置文件")
    import_export_layout = QHBoxLayout(import_export_group)

    load_btn = QPushButton("📂 导入配置")
    save_btn = QPushButton("💾 导出配置")

    load_btn.clicked.connect(load_collider_config)
    save_btn.clicked.connect(save_collider_config)

    import_export_layout.addWidget(load_btn)
    import_export_layout.addWidget(save_btn)

    # 插入到控制面板的适当位置
    control_layout.insertWidget(1, import_export_group)
def beam1_button_click():
    current_selection = simulator_state['beam1_particles']
    dialog = QDialog(window)
    dialog.setWindowTitle("选择束流1粒子")
    dialog.setModal(True)
    dialog.setFixedSize(300, 400)
    layout = QVBoxLayout()
    label = QLabel("选择粒子类型 (可多选):")
    layout.addWidget(label)
    list_widget = QListWidget()
    list_widget.setSelectionMode(QListWidget.MultiSelection)
    particle_names = list(particle_data.keys())
    for particle in particle_names:
        item = QListWidgetItem(f"{particle} ({particle_data[particle][0]})")
        item.setData(Qt.UserRole, particle)
        list_widget.addItem(item)
        if current_selection and particle in current_selection:
            item.setSelected(True)
    layout.addWidget(list_widget)
    button_layout = QHBoxLayout()
    ok_button = QPushButton("确定")
    cancel_button = QPushButton("取消")
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)
    dialog.setLayout(layout)
    if dialog.exec_() == QDialog.Accepted:
        selected = []
        for item in list_widget.selectedItems():
            selected.append(item.data(Qt.UserRole))
        if selected:
            simulator_state['beam1_particles'] = selected
            labels = [particle_data[p][0] for p in selected]
            label_text = "/".join(labels) if len(labels) <= 3 else f"{len(labels)}种粒子"
            beam1_label.setText(label_text)

def beam2_button_click():
    current_selection = simulator_state['beam2_particles']
    dialog = QDialog(window)
    dialog.setWindowTitle("选择束流2粒子")
    dialog.setModal(True)
    dialog.setFixedSize(300, 400)
    layout = QVBoxLayout()
    label = QLabel("选择粒子类型 (可多选):")
    layout.addWidget(label)
    list_widget = QListWidget()
    list_widget.setSelectionMode(QListWidget.MultiSelection)
    particle_names = list(particle_data.keys())
    for particle in particle_names:
        item = QListWidgetItem(f"{particle} ({particle_data[particle][0]})")
        item.setData(Qt.UserRole, particle)
        list_widget.addItem(item)
        if current_selection and particle in current_selection:
            item.setSelected(True)
    layout.addWidget(list_widget)
    button_layout = QHBoxLayout()
    ok_button = QPushButton("确定")
    cancel_button = QPushButton("取消")
    ok_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)
    button_layout.addWidget(ok_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)
    dialog.setLayout(layout)
    if dialog.exec_() == QDialog.Accepted:
        selected = []
        for item in list_widget.selectedItems():
            selected.append(item.data(Qt.UserRole))
        if selected:
            simulator_state['beam2_particles'] = selected
            labels = [particle_data[p][0] for p in selected]
            label_text = "/".join(labels) if len(labels) <= 3 else f"{len(labels)}种粒子"
            beam2_label.setText(label_text)

def start_simulation():
    global is_running
    if not is_running:
        is_running = True
        timer.start(50 // simulation_speed)
        start_btn.setText("⏵ 运行中...")

def pause_simulation():
    global is_running
    if is_running:
        is_running = False
        timer.stop()
        start_btn.setText("▶ 开始模拟")

def reset_simulation():
    global is_running
    is_running = False
    timer.stop()
    simulator_state['particles'] = []
    simulator_state['collision_events'] = []
    simulator_state['entangled_pairs'] = []
    simulator_state['time'] = 0.0
    simulator_state['event_counter'] = 0
    simulator_state['particle_counter'] = 0
    simulator_state['collision_distance'] = collision_dist_spin.value()
    simulator_state['annihilation_probability'] = annihilation_prob_spin.value()
    simulator_state['particle_creation_probability'] = creation_prob_spin.value()
    simulator_state['beam1_energy'] = beam1_energy_spin.value()
    simulator_state['beam2_energy'] = beam2_energy_spin.value()
    simulator_state['beam_spread'] = beam_spread_spin.value()
    simulator_state['momentum_spread'] = momentum_spread_spin.value()

    beam1_types = simulator_state['beam1_particles']
    beam2_types = simulator_state['beam2_particles']
    if not beam1_types:
        beam1_types = ["PROTON"]
    if not beam2_types:
        beam2_types = ["PROTON"]

    for i in range(simulator_state['num_particles']):
        p_type1 = random.choice(beam1_types)
        momentum1 = np.array([
            simulator_state['beam1_energy'],
            random.gauss(0, simulator_state['momentum_spread']),
            random.gauss(0, simulator_state['momentum_spread'])
        ])
        position1 = np.array([
            -8,
            random.gauss(0, simulator_state['beam_spread']),
            random.gauss(0, simulator_state['beam_spread'])
        ])
        particle1 = {
            'particle_id': simulator_state['particle_counter'],
            'particle_type': p_type1,
            'position': position1,
            'momentum': momentum1,
            'mass': particle_data[p_type1][1],
            'charge': particle_data[p_type1][2],
            'lifetime': particle_data[p_type1][3],
            'spin': random.choice(["UP", "DOWN", "LEFT", "RIGHT"]),
            'trajectory': [position1.copy()],
            'creation_time': 0.0,
            'velocity_history': []
        }
        particle1['energy'] = math.sqrt(np.linalg.norm(momentum1) ** 2 + particle1['mass'] ** 2)
        simulator_state['particle_counter'] += 1
        simulator_state['particles'].append(particle1)

        p_type2 = random.choice(beam2_types)
        momentum2 = np.array([
            -simulator_state['beam2_energy'],
            random.gauss(0, simulator_state['momentum_spread']),
            random.gauss(0, simulator_state['momentum_spread'])
        ])
        position2 = np.array([
            8,
            random.gauss(0, simulator_state['beam_spread']),
            random.gauss(0, simulator_state['beam_spread'])
        ])
        particle2 = {
            'particle_id': simulator_state['particle_counter'],
            'particle_type': p_type2,
            'position': position2,
            'momentum': momentum2,
            'mass': particle_data[p_type2][1],
            'charge': particle_data[p_type2][2],
            'lifetime': particle_data[p_type2][3],
            'spin': random.choice(["UP", "DOWN", "LEFT", "RIGHT"]),
            'trajectory': [position2.copy()],
            'creation_time': 0.0,
            'velocity_history': []
        }
        particle2['energy'] = math.sqrt(np.linalg.norm(momentum2) ** 2 + particle2['mass'] ** 2)
        simulator_state['particle_counter'] += 1
        simulator_state['particles'].append(particle2)

    for item in particle_items + trajectory_items + collision_items + info_items:
        gl_widget.removeItem(item)
    particle_items.clear()
    trajectory_items.clear()
    collision_items.clear()
    info_items.clear()

def update_speed(value):
    global simulation_speed
    simulation_speed = value
    speed_label.setText(f"速度: {value}x")
    if is_running:
        timer.start(50 // simulation_speed)

def update_physics_params():
    simulator_state['collision_distance'] = collision_dist_spin.value()
    simulator_state['annihilation_probability'] = annihilation_prob_spin.value()
    simulator_state['particle_creation_probability'] = creation_prob_spin.value()

def update_particle_count():
    if not is_running:
        simulator_state['num_particles'] = particle_count_spin.value()

def update_beam_params():
    simulator_state['beam1_energy'] = beam1_energy_spin.value()
    simulator_state['beam2_energy'] = beam2_energy_spin.value()
    simulator_state['beam_spread'] = beam_spread_spin.value()
    simulator_state['momentum_spread'] = momentum_spread_spin.value()

def update_visualization():
    for _ in range(simulation_speed):
        dt = 1e-12
        for particle in simulator_state['particles']:
            velocity = particle['momentum'] / particle['energy'] if particle['energy'] > 0 else np.array([0, 0, 0])
            particle['position'] += velocity * dt
            particle['trajectory'].append(particle['position'].copy())
            particle['velocity_history'].append(np.linalg.norm(velocity))

        particles_to_remove = set()
        new_particles = []

        for i in range(len(simulator_state['particles'])):
            if i in particles_to_remove:
                continue
            for j in range(i + 1, len(simulator_state['particles'])):
                if j in particles_to_remove or i in particles_to_remove:
                    continue

                p1, p2 = simulator_state['particles'][i], simulator_state['particles'][j]
                if np.linalg.norm(p1['position'] - p2['position']) > simulator_state['collision_distance']:
                    continue

                antiparticle_pairs = [
                    ("ELECTRON", "POSITRON"),
                    ("MUON", "ANTIMUON"),
                    ("PROTON", "ANTIPROTON"),
                ]
                annihilation_occurred = False
                for pair in antiparticle_pairs:
                    if (p1['particle_type'] == pair[0] and p2['particle_type'] == pair[1]) or \
                            (p1['particle_type'] == pair[1] and p2['particle_type'] == pair[0]):
                        annihilation_occurred = random.random() < simulator_state['annihilation_probability']
                        break

                particles_in = [p1, p2]
                particles_out = []
                event_type = "elastic"

                if annihilation_occurred:
                    total_energy = p1['energy'] + p2['energy']
                    num_photons = random.randint(2, 6)
                    for k in range(num_photons):
                        theta = random.uniform(0, 2 * math.pi)
                        phi = random.uniform(0, math.pi)
                        photon_energy = total_energy / num_photons * random.uniform(0.7, 1.3)
                        momentum = photon_energy * np.array([
                            math.sin(phi) * math.cos(theta),
                            math.sin(phi) * math.sin(theta),
                            math.cos(phi)
                        ])
                        photon = {
                            'particle_id': simulator_state['particle_counter'],
                            'particle_type': "PHOTON",
                            'position': (p1['position'] + p2['position']) / 2,
                            'momentum': momentum,
                            'mass': 0,
                            'charge': 0,
                            'lifetime': 1e30,
                            'spin': random.choice(["UP", "DOWN", "LEFT", "RIGHT"]),
                            'trajectory': [(p1['position'] + p2['position']) / 2],
                            'creation_time': simulator_state['time'],
                            'velocity_history': []
                        }
                        photon['energy'] = photon_energy
                        simulator_state['particle_counter'] += 1
                        particles_out.append(photon)
                    event_type = "annihilation"
                    if len(particles_out) >= 2:
                        entangled_pair = {
                            'pair_id': len(simulator_state['entangled_pairs']),
                            'particle1_id': particles_out[0]['particle_id'],
                            'particle2_id': particles_out[1]['particle_id'],
                            'spin_correlation': random.uniform(0.8, 1.0),
                            'creation_time': simulator_state['time']
                        }
                        simulator_state['entangled_pairs'].append(entangled_pair)
                elif random.random() < simulator_state['particle_creation_probability']:
                    new_particle_types = ["PION_PLUS", "PION_MINUS", "HIGGS", "GLUON", "NEUTRON"]
                    new_particle_type = random.choice(new_particle_types)
                    total_energy = p1['energy'] + p2['energy']
                    theta = random.uniform(0, 2 * math.pi)
                    phi = random.uniform(0, math.pi)
                    new_energy = total_energy * 0.6
                    momentum = new_energy * np.array([
                        math.sin(phi) * math.cos(theta),
                        math.sin(phi) * math.sin(theta),
                        math.cos(phi)
                    ])
                    new_particle = {
                        'particle_id': simulator_state['particle_counter'],
                        'particle_type': new_particle_type,
                        'position': (p1['position'] + p2['position']) / 2,
                        'momentum': momentum,
                        'mass': particle_data[new_particle_type][1],
                        'charge': particle_data[new_particle_type][2],
                        'lifetime': particle_data[new_particle_type][3],
                        'spin': random.choice(["UP", "DOWN", "LEFT", "RIGHT"]),
                        'trajectory': [(p1['position'] + p2['position']) / 2],
                        'creation_time': simulator_state['time'],
                        'velocity_history': []
                    }
                    new_particle['energy'] = new_energy
                    simulator_state['particle_counter'] += 1
                    particles_out = [new_particle]
                    event_type = "particle_creation"
                else:
                    transfer_fraction = random.uniform(0.1, 0.4)
                    momentum_transfer = transfer_fraction * (p1['momentum'] - p2['momentum'])
                    p1['momentum'] -= momentum_transfer
                    p2['momentum'] += momentum_transfer
                    p1['energy'] = math.sqrt(np.linalg.norm(p1['momentum']) ** 2 + p1['mass'] ** 2)
                    p2['energy'] = math.sqrt(np.linalg.norm(p2['momentum']) ** 2 + p2['mass'] ** 2)
                    particles_out = [p1, p2]

                event = {
                    'event_id': simulator_state['event_counter'],
                    'particles_in': particles_in,
                    'particles_out': particles_out,
                    'position': (p1['position'] + p2['position']) / 2,
                    'energy': p1['energy'] + p2['energy'],
                    'timestamp': simulator_state['time'],
                    'event_type': event_type
                }

                simulator_state['event_counter'] += 1
                simulator_state['collision_events'].append(event)
                particles_to_remove.update([i, j])
                new_particles.extend(particles_out)
                break

        for idx in sorted(particles_to_remove, reverse=True):
            if idx < len(simulator_state['particles']):
                simulator_state['particles'].pop(idx)

        simulator_state['particles'].extend(new_particles)
        simulator_state['time'] += dt

    for item in particle_items + trajectory_items + collision_items + info_items:
        gl_widget.removeItem(item)
    particle_items.clear()
    trajectory_items.clear()
    collision_items.clear()
    info_items.clear()

    particle_positions = []
    particle_colors = []
    particle_sizes = []

    for particle in simulator_state['particles']:
        pos = particle['position']
        color = particle_data[particle['particle_type']][5]
        size = 6 + particle['energy'] * 3

        particle_positions.append(pos)
        particle_colors.append(color)
        particle_sizes.append(size)

        if show_trajectories.isChecked() and len(particle['trajectory']) > 1:
            trajectory = np.array(particle['trajectory'][-15:])
            trajectory_item = gl.GLLinePlotItem(
                pos=trajectory,
                color=color,
                width=2,
                antialias=True
            )
            gl_widget.addItem(trajectory_item)
            trajectory_items.append(trajectory_item)

    if particle_positions:
        particles_item = gl.GLScatterPlotItem(
            pos=np.array(particle_positions),
            color=np.array(particle_colors),
            size=np.array(particle_sizes)
        )
        gl_widget.addItem(particles_item)
        particle_items.append(particles_item)

    if show_collision_rings.isChecked():
        recent_collisions = simulator_state['collision_events'][-8:]
        collision_positions = []
        collision_colors = []

        for event in recent_collisions:
            collision_positions.append(event['position'])
            if event['event_type'] == "annihilation":
                collision_colors.append((1, 0, 0, 0.8))
            elif event['event_type'] == "particle_creation":
                collision_colors.append((0, 1, 0, 0.8))
            else:
                collision_colors.append((1, 1, 0, 0.8))

            ring_radius = 0.8 + event['energy'] * 0.2
            theta = np.linspace(0, 2 * np.pi, 25)
            x = event['position'][0] + ring_radius * np.cos(theta)
            y = event['position'][1] + ring_radius * np.sin(theta)
            z = np.full_like(x, event['position'][2])

            ring_pos = np.column_stack([x, y, z])
            ring_item = gl.GLLinePlotItem(
                pos=ring_pos,
                color=collision_colors[-1],
                width=4
            )
            gl_widget.addItem(ring_item)
            collision_items.append(ring_item)

        if collision_positions:
            collisions_item = gl.GLScatterPlotItem(
                pos=np.array(collision_positions),
                color=np.array(collision_colors),
                size=25
            )
            gl_widget.addItem(collisions_item)
            collision_items.append(collisions_item)

    if show_particle_info.isChecked():
        stats_text = f"""对撞模拟状态
时间: {simulator_state['time']:.2e} s
粒子数: {len(simulator_state['particles'])}
碰撞事件: {len(simulator_state['collision_events'])}
纠缠对: {len(simulator_state['entangled_pairs'])}
速度: {simulation_speed}x"""

        stats_text_item = gl.GLTextItem(pos=(8, 6, 0), text=stats_text, color=(1, 1, 1, 1))
        gl_widget.addItem(stats_text_item)
        info_items.append(stats_text_item)

        particle_stats = defaultdict(int)
        for particle in simulator_state['particles']:
            particle_stats[particle_data[particle['particle_type']][0]] += 1

        stats_details = "=== 粒子分布 ===\n"
        for symbol, count in sorted(particle_stats.items(), key=lambda x: x[1], reverse=True):
            stats_details += f"{symbol}: {count}\n"

        if simulator_state['collision_events']:
            latest = simulator_state['collision_events'][-1]
            stats_details += f"\n=== 最近碰撞 ===\n"
            stats_details += f"类型: {latest['event_type']}\n"
            stats_details += f"能量: {latest['energy']:.1f} GeV\n"
            stats_details += f"粒子: {len(latest['particles_in'])} → {len(latest['particles_out'])}"

        stats_label.setText(stats_details)

beam1_button.clicked.connect(beam1_button_click)
beam2_button.clicked.connect(beam2_button_click)
start_btn.clicked.connect(start_simulation)
pause_btn.clicked.connect(pause_simulation)
reset_btn.clicked.connect(reset_simulation)
speed_slider.valueChanged.connect(update_speed)
collision_dist_spin.valueChanged.connect(update_physics_params)
annihilation_prob_spin.valueChanged.connect(update_physics_params)
creation_prob_spin.valueChanged.connect(update_physics_params)
particle_count_spin.valueChanged.connect(update_particle_count)
beam1_energy_spin.valueChanged.connect(update_beam_params)
beam2_energy_spin.valueChanged.connect(update_beam_params)
beam_spread_spin.valueChanged.connect(update_beam_params)
momentum_spread_spin.valueChanged.connect(update_beam_params)
timer.timeout.connect(update_visualization)
window.show()
add_collider_import_export_buttons()
sys.exit(app.exec_())