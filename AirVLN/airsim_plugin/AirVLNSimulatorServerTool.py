import argparse
import threading
import msgpackrpc
from pathlib import Path
import glob
import time
import os
import json
import sys
import subprocess
import errno
import signal
import copy


AIRSIM_SETTINGS_TEMPLATE = {
    "SeeDocsAt": "https://github.com/Microsoft/AirSim/blob/master/docs/settings.md",
    "SettingsVersion": 1.2,
    "SimMode": "ComputerVision", # ComputerVision / Multirotor
    "ViewMode": "NoDisplay", # Fpv / NoDisplay
    "ClockSpeed": 1,
    # "LocalHostIp": "127.0.0.1",
    # "ApiServerPort": 10000,
    "CameraDefaults": {
        "CaptureSettings": [
            {
                "ImageType": 0,
                "Width": 224,
                "Height": 224,
                "FOV_Degrees": 90,
                "AutoExposureMaxBrightness": 1,
                "AutoExposureMinBrightness": 0.03
            },
            {
                "ImageType": 2,
                "Width": 256,
                "Height": 256,
                "FOV_Degrees": 90,
                "AutoExposureMaxBrightness": 1,
                "AutoExposureMinBrightness": 0.03
            },
            {
                "ImageType": 3,
                "Width": 256,
                "Height": 256,
                "FOV_Degrees": 90,
                "AutoExposureMaxBrightness": 1,
                "AutoExposureMinBrightness": 0.03
            }
        ],
        "X": 0,
        "Y": 0,
        "Z": 0,
        "Pitch": 0,
        "Roll": 0,
        "Yaw": 0
    },
    "Recording": {
        "RecordInterval": 0.001,
        "Enabled": False,
        "Cameras": []
    },
    "SubWindows": [],
    "Vehicles": {}
}


def create_drones(drone_num_per_env=1, show_scene=False, uav_mode=False) -> dict:
    # ����һ���ֵ䣬���ݽṹ�� AirSim settings.json �ļ�һ��
    airsim_settings = copy.deepcopy(AIRSIM_SETTINGS_TEMPLATE)

    if show_scene == True:
        airsim_settings['ViewMode'] = 'Fpv'
    else:
        airsim_settings['ViewMode'] = 'NoDisplay'

    if uav_mode == True:
        airsim_settings['SimMode'] = 'Multirotor'
        airsim_settings['PhysicsEngineName'] = 'ExternalPhysicsEngine'
    else: # �����������棬ֻ����ͼ��ɼ�
        airsim_settings['SimMode'] = 'ComputerVision'


    # create drone objects
    for i in range(drone_num_per_env):
        drone_name = 'Drone_' + str(i+1)

        airsim_settings['Vehicles'][str(drone_name)] = {}

        drone = {
            "VehicleType": "ComputerVision",
            "Cameras": {
                "front_0": {
                    "CaptureSettings": [
                        {
                            "ImageType": 0,
                            "Width": 224,
                            "Height": 224,
                            "FOV_Degrees": 90,
                            "AutoExposureMaxBrightness": 1,
                            "AutoExposureMinBrightness": 0.03
                        },
                        {
                            "ImageType": 2,
                            "Width": 256,
                            "Height": 256,
                            "FOV_Degrees": 90,
                            "AutoExposureMaxBrightness": 1,
                            "AutoExposureMinBrightness": 0.03
                        },
                        {
                            "ImageType": 3,
                            "Width": 256,
                            "Height": 256,
                            "FOV_Degrees": 90,
                            "AutoExposureMaxBrightness": 1,
                            "AutoExposureMinBrightness": 0.03
                        }
                    ],
                    "X": 0.5, "Y": 0, "Z": 0,
                    "Pitch": 0, "Roll": 0, "Yaw": 0
                }
            },
            "X": 0, "Y": 0, "Z": 0,
            "Pitch": 0, "Roll": 0, "Yaw": 0
        }

        if airsim_settings['SimMode'] == 'ComputerVision':
            drone['VehicleType'] = 'ComputerVision'
        elif airsim_settings['SimMode'] == 'Multirotor':
            drone['VehicleType'] = 'SimpleFlight'
        else:
            raise NotImplementedError

        airsim_settings['Vehicles'][str(drone_name)] = copy.deepcopy(drone)

    return airsim_settings


def pid_exists(pid) -> bool: # is pid exists 
    """
    Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False

    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def FromPortGetPid(port: int): # �ݶ˿ں� port����ѯ�ĸ������ڼ����ö˿ڣ����������� PID�����̺ţ�
    subprocess_execute = "netstat -nlp | grep {}".format(
        port,
    )

    try:
        p = subprocess.Popen(
            subprocess_execute,
            stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            shell=True,
        ) # �����ӽ������� shell ����������
    except Exception as e:
        print(
            "{}\t{}\t{}".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
                'FromPortGetPid',
                e,
            )
        )
        return None
    except:
        return None

    pid = None
    for line in iter(p.stdout.readline, b''):
        line = str(line, encoding="utf-8")
        if 'tcp' in line:
            pid = line.strip().split()[-1].split('/')[0]
            try:
                pid = int(pid)
            except:
                pid = None
            break

    try:
        # os.system(("kill -9 {}".format(p.pid)))
        os.kill(p.pid, signal.SIGKILL)
    except:
        pass

    return pid


def KillPid(pid) -> None: 
    if pid is None or not isinstance(pid, int):
        print('pid is not int')
        return

    while pid_exists(pid):
        try:
            # os.system(("kill -9 {}".format(pid)))
            os.kill(pid, signal.SIGKILL)
        except Exception as e:
            pass
        time.sleep(0.5)

    return


def KillPorts(ports) -> None: # ����ɱ��ռ����ָ���˿ڵĽ���
    threads = []

    def _kill_port(index, port):
        pid = FromPortGetPid(port)
        KillPid(pid)

    for index, port in enumerate(ports):
        thread = threading.Thread(target=_kill_port, args=(index, port))
        threads.append(thread)
    for thread in threads:
        thread.setDaemon(True)
        thread.start()
    for thread in threads:
        thread.join()
    threads = []

    return


def KillAirVLN() -> None:
    subprocess_execute = "pkill -9 AirVLN"

    try:
        p = subprocess.Popen(
            subprocess_execute,
            stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            shell=True,
        ) # �� Python ������һ���µ��ӽ��̣�ִ��ָ���� shell ��������������������׼����ʹ��������
    except Exception as e:
        print(
            "{}\t{}\t{}".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
                'KillAirVLN',
                e,
            )
        )
        return
    except:
        return

    try:
        # os.system(("kill -9 {}".format(p.pid)))
        os.kill(p.pid, signal.SIGKILL)
    except:
        pass

    time.sleep(1)
    return


class EventHandler(object):
    def __init__(self):
        scene_ports = []
        for i in range(1000):
            scene_ports.append(
                int(args.port) + (i+1)
            )
        self.scene_ports = scene_ports

        scene_gpus = []
        while len(scene_gpus) < 100:
            scene_gpus += GPU_IDS.copy()
        self.scene_gpus = scene_gpus

        self.scene_used_ports = []

    def ping(self) -> bool:
        return True

    def _open_scenes(self, ip: str , scen_ids: list):
        print(
            "{}\tSTART closing scenes ".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            )
        )
        KillPorts(self.scene_used_ports)
        self.scene_used_ports = []
        # KillAirVLN()
        print(
            "{}\tEND closing scenes ".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            )
        )


        # Occupied airsim port 1 �Ӻ�ѡ�˿���ѡ��δ��ռ�õ�
        ports = []
        index = 0
        while len(ports) < len(scen_ids):
            pid = FromPortGetPid(self.scene_ports[index])
            if pid is None or not isinstance(pid, int):
                ports.append(self.scene_ports[index])
            index += 1

        KillPorts(ports)


        # Occupied GPU 2 Ϊÿ���������� GPU
        gpus = [self.scene_gpus[index] for index in range(len(scen_ids))]


        # search scene path 3 ���뻷����·��
        choose_env_exe_paths = []
        for scen_id in scen_ids: # v1, v2
            if str(scen_id).lower() == 'none':
                choose_env_exe_paths.append(None)
                continue
            #SEARCH_ENVs_PATH = ENVs
            # /remote-home/xhl/9_UAV_VLN/AirVLN_ws/ENVs/**/env_01/LinuxNoEditor/AirVLN.sh
            res = glob.glob((str(SEARCH_ENVs_PATH) + '/**/' + 'env_' + str(scen_id) + '/LinuxNoEditor/AirVLN.sh'), recursive=True)
            if len(res) > 0:
                choose_env_exe_paths.append(res[0])
            else:
                print(f'can not find scene file: {scen_id}')
                raise KeyError

        
        p_s = []
        for index in range(len(scen_ids)):
            # airsim settings 4
            airsim_settings = create_drones()
            airsim_settings['ApiServerPort'] = int(ports[index])
            airsim_settings_write_content = json.dumps(airsim_settings)
            if not os.path.exists(str(CWD_DIR / 'airsim_plugin/settings' / str(index+1))):
                os.makedirs(str(CWD_DIR / 'airsim_plugin/settings' / str(index+1)), exist_ok=True)
            with open(str(CWD_DIR / 'airsim_plugin/settings' / str(index+1) / 'settings.json'), 'w', encoding='utf-8') as dump_f:
                dump_f.write(airsim_settings_write_content) # ��ͬenv��Ӧ��ͬ��settings.json�ļ�


            # open scene 5
            if choose_env_exe_paths[index] is None:
                p_s.append(None)
                continue
            else:
                # [PATCH] UE4 refuses to run as root, so launch as the airvln user.
                # Root cause of multi-GPU failure: Vulkan default ICD list includes Mesa llvmpipe
                # (software CPU renderer) which appears as device index 0, shifting NVIDIA devices
                # to indices 1,2,3. -GraphicsAdapter=1 and =2 hit wrong GPUs or fail.
                # Fix: set VK_ICD_FILENAMES to nvidia_icd.json only → devices 0,1,2 = 3×RTX3060.
                # Verified: DISPLAY=:1 VK_ICD_FILENAMES=.../nvidia_icd.json vulkaninfo --summary
                # shows exactly 3 DISCRETE_GPU devices matching nvidia-smi GPU 0,1,2 by PCI bus.
                # ORIGINAL:
                # subprocess_execute = "su airvln -c 'DISPLAY=:1 CUDA_VISIBLE_DEVICES={gpu} bash {exe} -RenderOffscreen -NoSound -NoVSync -GraphicsAdapter=0 --settings {settings}'".format(
                #     gpu=gpus[index],
                #     exe=choose_env_exe_paths[index],
                #     settings=str(CWD_DIR / 'airsim_plugin/settings' / str(index+1) / 'settings.json'),
                # )
                # PATCH ATTEMPT KEPT FOR REFERENCE:
                # subprocess_execute = "su airvln -c 'DISPLAY=:1 bash {exe} -RenderOffscreen -NoSound -NoVSync -GraphicsAdapter={gpu} --settings {settings}'".format(
                #     gpu=gpus[index],
                #     exe=choose_env_exe_paths[index],
                #     settings=str(CWD_DIR / 'airsim_plugin/settings' / str(index+1) / 'settings.json'),
                # )
                # FIX: Force NVIDIA-only Vulkan ICD so all 3 GPUs are enumerated
                # (without this, the Mesa software rasterizer llvmpipe appears as adapter 0
                # and -GraphicsAdapter=1 is NVIDIA GPU 0, -GraphicsAdapter=2 is GPU 1, etc.)
                # With VK_ICD_FILENAMES set to nvidia_icd.json only:
                #   -GraphicsAdapter=0 → NVIDIA GPU 0 (pciBus 0x05)
                #   -GraphicsAdapter=1 → NVIDIA GPU 1 (pciBus 0x82)
                #   -GraphicsAdapter=2 → NVIDIA GPU 2 (pciBus 0x83)
                # Verified with: DISPLAY=:1 VK_ICD_FILENAMES=... vulkaninfo --summary
                subprocess_execute = (
                    "su airvln -c 'DISPLAY=:1 "
                    "VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json "
                    "bash {exe} -RenderOffscreen -NoSound -NoVSync "
                    "-GraphicsAdapter={gpu} --settings {settings}'"
                ).format(
                    gpu=gpus[index],
                    exe=choose_env_exe_paths[index],
                    settings=str(CWD_DIR / 'airsim_plugin/settings' / str(index+1) / 'settings.json'),
                )

                try:
                    p = subprocess.Popen(
                        subprocess_execute,
                        stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        shell=True,
                    )
                    p_s.append(p)
                except Exception as e:
                    print(
                        "{}\t{}".format(
                            str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
                            e,
                        )
                    )
                    return False, None
                except:
                    return False, None
        time.sleep(3)

        # check
        threads = []

        def _check_scene(index, p): # Opening 0-th scene (scene 01)	gpu:0
            if p is None:
                print(
                    "{}\tOpening {}-th scene (scene {})\tgpu:{}".format(
                        str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
                        index,
                        None,
                        gpus[index],
                    )
                )
                return

            for line in iter(p.stdout.readline, b''):
                if 'Drone_' in str(line):
                    break

            try:
                p.terminate()
                # os.system(("kill -9 {}".format(p.pid)))
                os.kill(p.pid, signal.SIGKILL)
            except:
                pass

            print(
                "{}\tOpening {}-th scene (scene {})\tgpu:{}".format(
                    str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
                    index,
                    scen_ids[index],
                    gpus[index],
                )
            )
            return

        for index, p in enumerate(p_s):
            thread = threading.Thread(target=_check_scene, args=(index, p))
            threads.append(thread)
        for thread in threads:
            thread.setDaemon(True)
            thread.start()
        for thread in threads:
            thread.join()
        threads = []

        # ChangeNice(ports)

        self.scene_used_ports += copy.deepcopy(ports)

        return True, (ip, ports)

    def reopen_scenes(self, ip: str, scen_ids: list):
        print(
            "{}\tSTART reopen_scenes".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            )
        )
        try:
            result = self._open_scenes(ip, scen_ids)
        except Exception as e:
            print(e)
            result = False, None
        print(
            "{}\tEND reopen_scenes".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            )
        )
        return result

    def close_scenes(self, ip: str) -> bool:
        print(
            "{}\tSTART close_scenes".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            )
        )

        try:
            KillPorts(self.scene_used_ports)
            self.scene_used_ports = []
            # KillPorts(self.scene_ports)
            # KillAirVLN()

            result = True
        except Exception as e:
            print(e)
            result = False

        print(
            "{}\tEND close_scenes".format(
                str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            )
        )
        return result

# ���������� RPC ����Ȼ������ӵ���̨�߳������У�������������
def serve_background(server, daemon=False):
    def _start_server(server):
        server.start()
        server.close()

    t = threading.Thread(target=_start_server, args=(server,))
    t.setDaemon(daemon)
    t.start()
    return t


def serve(daemon=False):
    try:
        server = msgpackrpc.Server(EventHandler())
        addr = msgpackrpc.Address(HOST, PORT)
        server.listen(addr)

        thread = serve_background(server, daemon)

        return addr, server, thread
    except Exception as err:
        print(err)
        pass


if __name__ == '__main__':
    # Argument
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gpus",
        type=str,
        default='0',
    )
    parser.add_argument(
        "--port",
        type=int,
        default=30000,
        help='server port'
    )
    args = parser.parse_args()


    HOST = '127.0.0.1'
    PORT = int(args.port)

    CWD_DIR = Path(str(os.getcwd())).resolve() # AirVLN_ws/AirVLN/airsim_plugin
    PROJECT_ROOT_DIR = CWD_DIR.parent # AirVLN_ws/AirVLN
    SEARCH_ENVs_PATH = PROJECT_ROOT_DIR / 'ENVs'

    
    assert os.path.exists(str(SEARCH_ENVs_PATH)), 'error'

    gpu_list = []
    gpus = str(args.gpus).split(',')
    for gpu in gpus:
        gpu_list.append(int(gpu.strip()))
    GPU_IDS = gpu_list.copy() # list of gpu ids

    # [PATCH] Map nvidia-smi GPU index to a Vulkan DRI_PRIME PCI selector.
    # ORIGINAL: only GPU_IDS existed, and launch used CUDA_VISIBLE_DEVICES.
    # CUDA_VISIBLE_DEVICES does not constrain Vulkan/UE4 on this server, so all scenes
    # landed on GPU 0. DRI_PRIME=pci-0000_xx_00_0 selects the intended NVIDIA adapter.
    GPU_DRI_PRIME_IDS = {}
    try:
        smi_output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,pci.bus_id",
                "--format=csv,noheader,nounits",
            ],
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in smi_output.strip().splitlines():
            gpu_index, pci_bus_id = [item.strip() for item in line.split(",", 1)]
            # [PATCH] nvidia-smi reports 00000000:83:00.0, while DRI_PRIME expects
            # pci-0000_83_00_0. Keep the original idea, but normalize the domain width.
            domain, bus, slot_func = pci_bus_id.lower().split(":")
            slot, func = slot_func.split(".")
            dri_prime_pci = "pci-{}_{}_{}_{}".format(domain[-4:], bus, slot, func)
            GPU_DRI_PRIME_IDS[int(gpu_index)] = dri_prime_pci
    except Exception as e:
        print("Failed to build GPU_DRI_PRIME_IDS, fallback to raw gpu ids: {}".format(e))
        GPU_DRI_PRIME_IDS = {gpu: str(gpu) for gpu in GPU_IDS}
    print("GPU_DRI_PRIME_IDS: {}".format(GPU_DRI_PRIME_IDS))

    
    addr, server, thread = serve()
    # import ipdb; ipdb.set_trace()
    print(f"start listening \t{addr._host}:{addr._port}")
