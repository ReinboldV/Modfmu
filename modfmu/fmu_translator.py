# -*- coding: utf-8 -*-
"""
Created on Thu Apr 07 13:54:47 2016

@author: vincent
"""
from builtins import TypeError

from modfmu.modelica import Package


class FMUTranslator:
    """Class to translate a Modelica model to FMU.
    """
    _translate_mos = '_translate.mos'

    _prestatements_fmu_dymola = """  Advanced.AllowMultipleInstances = true;
    OutputCPUtime = false;
    Advanced.CompileFMU32 = false;
    Advanced.CompileFMU64 = true;
    Advanced.CompileWith64 = 0;
    Advanced.AllowStringParameters = true;
    Advanced.FMI.xmlIgnoreProtected = true;
    Advanced.FMI.xmlIgnoreLocal = true;\
    Advanced.FMI.BlackBoxModelDescription = false;
    Advanced.FMI.CopyExternalResources = false; """

    def __init__(self, model_name, translator, fmu_name=None, output_directory=None, package_path=list(), reporter=None, modifier=""):

        """

        :type package_path: list
        """

        import buildingspy.io.reporter as rp
        import os

        if fmu_name is None:
            # self._fmu_name = os.path.splitext(model_name)[0]
            self._fmu_name = model_name.split('.')[-1]
        else:
            self._fmu_name = fmu_name

        if output_directory is None:
            output_directory = '.'
        else:
            self.output_directory = output_directory

        if isinstance(reporter, rp.Reporter):
            self._reporter = reporter
        else:
            log_fil_nam = os.path.join(output_directory, "fmu_translator.log")
            self._reporter = rp.Reporter(fileName=log_fil_nam)
            self._reporter.writeOutput('rp file is initiated')

        self.modifier = modifier
        self._model_name = model_name
        self._fmu_path = os.path.join(output_directory, self._fmu_name) + '.fmu'
        self._translator = translator
        self._preProcessing = list()
        self._postProcessing = list()
        self._dymola_log_file = 'dymola_translate.log'
        self.package_path = package_path

        for p in package_path:
            self.addpackagepath(p)

        # Translation options
        self._store_result = "false"
        self._fmi_version = "2"
        self._fmi_type = "all"
        self._include_src = "false"

        self._parameters_ = {}
        self._translator_ = {}

        #  self.setTimeOut(-1)
        self._modelica_exe = translator
        self._show_progress_bar = False
        self._show_gui = False
        self._exit_simulator = True

    @property
    def fmu_path(self):
        return self._fmu_path

    @fmu_path.setter
    def fmu_path(self, value):
        raise AttributeError('fmu_path attribute cannot be set by the user')

    @property
    def model_path(self):
        return self._model_name

    @model_path.setter
    def model_path(self, path):
        import os
        if not os.path.exists(path):
            msg = "Argument packagePath=%s does not exist." % path
            self._reporter.writeError(msg)
            raise ValueError(msg)
        else:
            self._model_name = path
            self._reporter.writeOutput('Path is set to {}'.format(path))

    @property
    def fmu_name(self):
        return self._fmu_name

    @fmu_name.setter
    def fmu_name(self, fmu_name):
        self._fmu_name = fmu_name

    @property
    def output_directory(self):
        """Returns the name of the output directory.

        :return: The name of the output directory.

        """
        return self._output_directory

    @output_directory.setter
    def output_directory(self, output_dir):
        """Sets the name of the output directory. 
        create it if does not exist
        
        :type output_dir: string
        """

        self._createDirectory(output_dir)
        self._output_directory = output_dir

    @property
    def fmi_type(self):
        """get the FMI type
        """
        return self._fmi_type

    @fmi_type.setter
    def fmi_type(self, fmi_type='cs'):
        if fmi_type in ['cs', 'all', 'me']:
            self._fmi_type = fmi_type
            self._reporter.writeOutput('fmiType is set to {}'.format(fmi_type))
        else:
            msg = "Unknown fmi type. Must be 'cs' or 'me' or 'all'"
            self._reporter.writeError(msg)
            raise ValueError(msg)

    def _createDirectory(self, directoryName):
        """ Creates the directory *directoryName*

        :param directoryName: The name of the directory

        This method validates the directory *directoryName* and if the
        argument is valid and write permissions exists, it creates the
        directory. Otherwise, a *ValueError* is raised.
        """
        import os

        if directoryName != '.':
            if len(directoryName) == 0:
                raise ValueError("Specified directory is not valid. Set to '.' for current directory.")
            # Try to create directory
            if not os.path.exists(directoryName):
                os.makedirs(directoryName)
            # Check write permission
            if not os.access(directoryName, os.W_OK):
                raise ValueError("Write permission to '" + directoryName + "' denied.")

    def addPostProcessingStatement(self, command):
        """Adds a post-processing statement to the simulation script.

        :param statement: A script statement.

        This will execute ``command`` after the simulation, and before
        the log file is written.
        """
        self._postProcessing.append(command)
        return

    def addPreProcessingStatement(self, command):
        """Adds a pre-processing statement to the simulation script.

        :param statement: A script statement.

        Usage: Type
           >>> from buildingspy.simulate.Simulator import Simulator
           >>> s=Simulator("myPackage.myModel", "dymola", packagePath="buildingspy/tests/MyModelicaLibrary")
           >>> s.addPreProcessingStatement("Advanced.StoreProtectedVariables = true;")
           >>> s.addPreProcessingStatement("Advanced.GenerateTimers = true;")

        This will execute the two statements after the ``openModel`` and
        before the ``simulateModel`` statement.
        """
        self._preProcessing.append(command)
        return

    def addpackagepath(self, packagePath):
        """ Set the path specified by ``packagePath``.

        :type packagePath: string
        :param packagePath: The path where the Modelica package to be loaded is located.

        It first checks whether the path exists and whether it is a directory.
        If both conditions are satisfied, the path is set.
        Otherwise, a ``ValueError`` is raised.
        """
        import os

        # Check whether the package Path parameter is correct
        if not os.path.exists(packagePath):
            msg = "Argument packagePath=%s does not exist." % packagePath
            raise ValueError(msg)

        if not os.path.isfile(packagePath):
            msg = "Argument packagePath=%s must be a file " % packagePath
            msg += "containing a Modelica package."
            raise ValueError(msg)

        # All the checks have been successfully passed
        self.addPreProcessingStatement('openModel("' + packagePath + '")')

    def setFmiVersion(self, fmiVersion='2'):
        """Set the FMI version
        
            :param fmiVersion: version of the fmi 
        """
        self._fmi_version = fmiVersion
        return

    def setTranslator(self, translator):
        """Sets the solver.

        :param solver: The name of the solver.

        The default solver is *radau*.
        """
        self._translator_.update(translator=translator)
        return

    def _get_dymola_commands(self):
        """
        Script that create a .mos file for translating the FMU 
        """

        #
        script = ''
        for p in self._preProcessing:
            script += '\n' + p
        script += '\n'
        script += 'cd("' + self._output_directory + '");\n'
        script += 'translateModelFMU("' + \
                  self.model_path + self.modifier + '",' + \
                  self._store_result + ',"' + \
                  self._fmu_name + '","' + \
                  self._fmi_version + '","' + \
                  self._fmi_type + '",' + \
                  self._include_src + ');\n'

        for p in self._postProcessing:
            script += p + '\n'

        script += 'savelog("{0}");\n'.format(self._dymola_log_file)

        if self._exit_simulator:
            script += "Modelica.Utilities.System.exit();\n"

        return script

    def translate_fmu(self):
        """ Translate model to FMU
        """
        import os
        from time import sleep

        runScriptName = os.path.join(self.output_directory, self._translate_mos)
        self._reporter.writeOutput('writing file {0}'.format(runScriptName))
        f = open(runScriptName, 'w')
        f.write(self._get_dymola_commands())
        f.close()
        self._reporter.writeOutput('running file {0}'.format(runScriptName))
        run_mos(runScriptName, directory=self.output_directory, modelica_exe=self._modelica_exe, timeout=100, showGUI=self._show_gui, showProgressBar=self._show_progress_bar)
        self._reporter.writeOutput('trying to read dymola log file :')
        try:
            sleep(0.1)
            with open(os.path.join(self.output_directory, self._dymola_log_file), 'r') as f:
                lines = f.readlines()
            line = '\t\t\t\t'.join(lines)
            self._reporter.writeOutput(line)
        except Exception:
            msg = 'Could not find the Dymola log file at {}'.format(os.path.join(self.output_directory, self._dymola_log_file))
            self._reporter.writeError(msg)


class FMUImport(object):
    _import_mos = '_import.mos'

    def __init__(self, pck, fmu_path, importer='Dymola', reporter=None):

        import buildingspy.io.reporter as rp
        import os

        # checking pck
        if type(pck) is Package:
            self.pck = pck
        else:
            msg = 'pck must be a modelica package'
            raise TypeError(msg)

        if isinstance(reporter, rp.Reporter):
            self._reporter = reporter
        elif reporter is None:
            log_fil_nam = os.path.join(pck.path, "fmu_importer.log")
            self._reporter = rp.Reporter(fileName=log_fil_nam)
            self._reporter.writeOutput('rp file is initiated')

        # checking fmu_path
        if os.path.exists(fmu_path) and fmu_path.endswith('.fmu'):
            self._fmu_path = fmu_path
            self._fmu_name = os.path.basename(fmu_path)
        else:
            msg = 'fmu_path must be pointing at an existing fmu file. Got %s instead' % fmu_path
            self._reporter.writeError(msg)
            raise FileNotFoundError(msg)

        self._MODELICA_EXE = importer
        self._exitSimulator = True
        self._showGUI = False
        self._showProgressBar = False

        self._preProcessing = list()
        self._postProcessing = list()

        self._dymola_log_file = 'dymola_import.log'

    def addPostProcessingStatement(self, command):
        """
        Adds a post-processing statement to the simulation script.

        :param command:  A script statement.

        This will execute ``command`` after the simulation, and before
        the log file is written.
        """

        self._postProcessing.append(command)

    def addPreProcessingStatement(self, command):
        """
        Adds a pre-processing statement to the simulation script.

        :param command: A script statement.

        This will execute the two statements after the ``openModel`` and
        before the ``simulateModel`` statement.
        """

        self._preProcessing.append(command)
        return

    def _get_dymola_commands(self):
        """
        Script that create a .mos file for translating the FMU 
        """

        import os

        script = ''
        for p in self._preProcessing:
            script += '\n' + p
        script += '\n'

        script += 'openModel("{}");\n'.format(os.path.join(self.pck.path, Package._package_file))
        script += 'cd("{}");\n'.format(self.pck.path)
        script += '  Advanced.FMI.CopyExternalResources = false;\n'
        script += '  Advanced.FMI.OverlappingIOThreshold = 6;\n'
        script += 'importFMU("{0}", false, false, false, "{1}");\n'.format(self._fmu_path.replace('\\', r'\\'), self.pck._modelica_name)

        for p in self._postProcessing:
            script += p + '\n'

        script += 'savelog("{}");\n'.format(self._dymola_log_file)

        if self._exitSimulator:
            script += "Modelica.Utilities.System.exit();\n"

        return script

    def import_fmu(self):
        """ 
        import FMU to modelica model
        """
        import os
        from time import sleep

        runScriptName = os.path.join(self.pck.path, self._import_mos)
        self._reporter.writeOutput('writing file {0}'.format(runScriptName))
        f = open(runScriptName, 'w')
        f.write(self._get_dymola_commands())
        f.close()
        self._reporter.writeOutput('running file {0}'.format(runScriptName))
        run_mos(runScriptName, directory=self.pck.path, modelica_exe=self._MODELICA_EXE, timeout=100, showGUI=self._showGUI, showProgressBar=self._showProgressBar)
        self._reporter.writeOutput('trying to read dymola log file :')

        try:
            sleep(0.2)
            with open(os.path.join(self.pck.path, self._dymola_log_file), 'r') as f:
                lines = f.readlines()
            line = '\t\t\t\t'.join(lines)
            self._reporter.writeOutput(line)
        except Exception:
            self._reporter.writeError('Could not find the Dymola log file')


def print_progress_bar(fraction_complete):
    """Prints a progress bar to the console.

    :param fraction_complete: The fraction of the time that is completed.

    """
    import sys
    nInc = 50
    count = int(nInc * fraction_complete)
    proBar = "|"
    for i in range(nInc):
        if i < count:
            proBar += "-"
        else:
            proBar += " "
    proBar += "|"
    print((proBar, int(fraction_complete * 100), "%\r",))
    sys.stdout.flush()


def is_executable(program):
    import os
    import platform

    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    # Add .exe, which is needed on Windows 7 to test existence
    # of the program
    if platform.system() == "Windows":
        program = program + ".exe"

    if is_exe(program):
        return True
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return True
    return False


def run_mos(mosFile, directory, modelica_exe='Dymola',
            timeout=60, showGUI=False, showProgressBar=False):
    """Runs a model translation or simulation.
    
    :param showGUI: 
    :param showProgressBar: 
    :param modelica_exe: 
    :param mosFile: The Modelica *mos* file name, including extension
    :param timeout: Time out in seconds
    :param directory
    """

    import sys
    import subprocess
    import time
    import datetime

    # Remove the working directory from the mosFile name.
    # This is needed for example if the simulation is run in a docker,
    # which may have a different file structure than the host.

    # List of command and arguments
    if showGUI:
        cmd = [modelica_exe, mosFile]
    else:
        cmd = [modelica_exe, mosFile, "/nowindow"]

    # Check if executable is on the path
    if not is_executable(cmd[0]):
        print(("Error: Did not find executable '", cmd[0], "'."))
        print("       Make sure it is on the PATH variable of your operating system.")
        exit(3)
    # Run command
    try:
        staTim = datetime.datetime.now()
        #            self._reporter.writeOutput("Starting simulation in '" +
        #                                        directory + "' at " +
        #                                        str(staTim))
        pro = subprocess.Popen(args=cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=False,
                               cwd=directory)
        killedProcess = False
        if timeout > 0:
            while pro.poll() is None:
                time.sleep(0.01)
                elapsedTime = (datetime.datetime.now() - staTim).seconds

                if elapsedTime > timeout:
                    # First, terminate the process. Then, if it is still
                    # running, kill the process

                    if showProgressBar and not killedProcess:
                        killedProcess = True
                        # This output needed because of the progress bar
                        sys.stdout.write("\n")

                        pro.terminate()
                    else:

                        pro.kill()
                else:
                    if showProgressBar:
                        fractionComplete = float(elapsedTime) / float(timeout)
                        print_progress_bar(fractionComplete)

        else:
            pro.wait()
        # This output is needed because of the progress bar
        if showProgressBar and not killedProcess:
            sys.stdout.write("\n")

        if not killedProcess:
            std_out = pro.stdout.read()
            std_err = pro.stderr.read()

    except OSError as e:
        print(("Execution of ", cmd, " failed:", e))


def translate_model(pck, model, fmu_name=None, fmu_dir_name='FMUs', report=None, modifier=""):
    import os
    import buildingspy.io.reporter as rp
    from modfmu.modelica import Package

    if not isinstance(report, rp.Reporter):
        log_fil_nam = os.path.join(pck.path, "package_fmu_translation.log")
        report = rp.Reporter(log_fil_nam)
        report.writeOutput('Initialisation of the log file')
        report.writeOutput('Creation of the FMUs sub package for translation and import of the FMUs')

    pck.add_subpackage(fmu_dir_name, order='first')
    fmu_dir = os.path.join(pck.path, fmu_dir_name)
    fmu_pck = Package(fmu_dir)

    if os.path.isfile(os.path.join(pck.path, model)) and model.endswith('.mo'):
        report.writeOutput('found the following modelica model to be translated : {}'.format(model))
        model_base = os.path.splitext(model)[0]  # name of the modelica file without extension
        model = '.'.join([pck._modelica_name, model_base])  # name of the model in modelica
        model_dir = os.path.join(pck.path, 'FMUs', model_base)
        fmutrans = FMUTranslator(model,
                                 translator='Dymola',
                                 fmu_name=fmu_name,
                                 modifier=modifier,
                                 output_directory=model_dir,
                                 package_path=[os.path.join(pck.adam, Package._package_file)],
                                 reporter=report)
        fmutrans.addPreProcessingStatement(FMUTranslator._prestatements_fmu_dymola)
        fmutrans.fmi_type = 'cs'
        fmutrans.setFmiVersion(fmiVersion='2')
        fmutrans.translate_fmu()

        if os.path.exists(model_dir) and os.path.exists(fmutrans.fmu_path):
            fmu_import = FMUImport(fmu_pck, fmutrans.fmu_path, reporter=report)
            fmu_import.import_fmu()
        else:
            msg = 'Something went wrong. check Dymola log file for more details.'
            report.writeWarning(msg)

    else:
        report.writeWarning('{} is not a modelica model'.format(model))


def translate_package(pck, fmu_dir_name='FMUs'):
    """
    Automated translation of all modelica models defined in a given package.

    First, a sub package for FMU export is created under pck_dir/fmu_dir. 
    Then, every modelica models found in the package are translated using Modfmu class and Dymola(default).
    To avoid compilation problems sub folder are created pck_dir/fmu_dir/model_name. 

    for each fmu exported, it is automatically imported in fmu_dir package using FMUImport class.

    :param pck : Package to be translated to FMU
    :param fmu_dir_name : name of the folder created in pck.path for FMUs 
    :type fmu_dir_name: str
    :type pck: Package
    """

    import os
    import buildingspy.io.reporter as rp
    from modfmu.modelica import Package

    log_fil_nam = os.path.join(pck.path, "package_fmu_translation.log")
    report = rp.Reporter(log_fil_nam)
    report.writeOutput('Initialisation of the log file')
    report.writeOutput('Creation of the FMUs sub package for translation and import of the FMUs')
    pck.add_subpackage(fmu_dir_name, order='first')
    fmu_dir = os.path.join(pck.path, fmu_dir_name)
    fmu_pck = Package(fmu_dir)  # modelica package for fmus export and import

    for m in os.listdir(pck.path):
        if os.path.isfile(os.path.join(pck.path, m)) and m.endswith('.mo'):
            report.writeOutput('found the following modelica model to be translated : {}'.format(m))
            model_base = os.path.splitext(m)[0]  # name of the modelica file without extension
            model = '.'.join([pck._modelica_name, model_base])  # name of the model in modelica
            model_dir = os.path.join(pck.path, 'FMUs', model_base)
            fmutrans = FMUTranslator(model, translator='Dymola', output_directory=model_dir, package_path=[os.path.join(pck.adam, Package._package_file)], reporter=report)
            fmutrans.addPreProcessingStatement(("  Advanced.AllowMultipleInstances = true;\n"
                                                "  OutputCPUtime = false;\n"
                                                "  Advanced.CompileFMU32 = false;\n"
                                                "  Advanced.CompileFMU64 = true;\n"
                                                "  Advanced.CompileWith64 = 0;\n"
                                                "  Advanced.AllowStringParameters = true;\n"
                                                "  Advanced.FMI.xmlIgnoreProtected = true;\n"
                                                "  Advanced.FMI.xmlIgnoreLocal = true;\n"
                                                "  Advanced.FMI.BlackBoxModelDescription = false;\n"
                                                "  Advanced.FMI.CopyExternalResources = false;\n"))
            fmutrans.fmi_type = 'cs'
            fmutrans.setFmiVersion(fmiVersion='2')
            fmutrans.translate_fmu()

            if os.path.exists(model_dir) and os.path.exists(fmutrans.fmu_path):
                fmu_import = FMUImport(fmu_pck, fmutrans.fmu_path, reporter=report)
                fmu_import.import_fmu()
            else:
                msg = 'Something went wrong. check Dymola log file for more details.'
                report.writeWarning(msg)

        else:
            report.writeWarning('{} is not a modelica model'.format(m))
