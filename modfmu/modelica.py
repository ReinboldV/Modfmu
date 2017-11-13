from tkinter import Pack


class Package(object):
    _package_file = 'package.mo'
    _package_order = 'package.order'

    def __init__(self, path):
        import os
        try:
            path = os.path.realpath(path)
        except Exception as e:
            raise e

        self._path = path
        self._name = path.split(os.path.sep)[-1]
        self._children = set()
        self._models = set()
        self._parents = set()
        self._adam = None

        if os.path.exists(self.path):  # si exists path
            #   si exists package.mo and package.order -> existing package
            if os.path.isfile(os.path.join(self.path, Package._package_file)) and \
                    os.path.isfile(os.path.join(self.path, Package._package_order)):
                self.scan_children()
                self.scan_parents()
            else:
                Package.create_package(self.path)
        else:  # create dir, package.mo, package.order
            try:
                os.mkdir(self.path)
                Package.create_package(self.path)
            except Exception as e:
                raise e

        self._parent_modelica_name = self.adam.split(os.path.sep)[-1]  # 'GenkNET'
        rel = os.path.relpath(self.path, self.adam)  # 'CoSimulation\\Components\\Neighborhoud'
        self._modelica_name = '.'.join([self._parent_modelica_name, '.'.join(rel.split(os.path.sep))])

        # if Package.is_modelica_package(parent_dir):
        #     self._parent = os.path.realpath(parent_dir)
        #     self._parent_modelica_name = self._parent.split(os.path.sep)[-1]  # 'GenkNET'
        #
        #     self._modelica_name = '.'.join([self._parent_modelica_name, '.'.join(rel.split(os.path.sep))])
        #
        # elif parent_dir is None:
        #     self._parent = None
        #     self._parent_modelica_name = None
        #     self._modelica_name = self._name
        #
        # else:
        #     raise ValueError('parent_dir must be a modelica package or None')

        self._package_file = os.path.join(path, Package._package_file)
        self._order_file = os.path.join(path, Package._package_order)

    @property
    def adam(self):
        return self._adam

    @adam.setter
    def adam(self, value):
        raise AttributeError('adam atribute cannot be set by the user.')

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, file):
        if str.endswith(file, '.mo'):
            self._models.add(file)

    @property
    def children(self):
        self.scan_children()
        return self._children

    @children.setter
    def children(self, pck_path):
        if Package.is_modelica_package(pck_path):
            self._children.add(pck_path)

    @property
    def parents(self):
        return self._parents

    @parents.setter
    def parents(self, value):
        if Package.is_modelica_package(value):
            self._parents.add(value)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        raise AttributeError('path attribute cannot be set by the user')

    @staticmethod
    def is_modelica_package(path):
        import os
        if path is None:
            return False

        if not os.path.exists(path) or not os.path.isdir(path):
            msg = 'The given path "%s" must be an existing directory' % path
            print(msg)
            return False

        if os.path.exists(os.path.join(path, Package._package_file)) and \
                os.path.isfile(os.path.join(path, Package._package_order)):
            return True
        else:
            return False

    @staticmethod
    def create_package(path):
        import os
        path = os.path.abspath(path)
        name = path.split(os.path.sep)[-1]
        parent = path.split(os.path.sep)[-2]
        with open(os.path.join(path, Package._package_file), 'w+') as f:
            f.write('within {} ; \n'.format(parent) +
                    'package {} ""\n'.format(name) +
                    '   extends Modelica.Icons.Package; \n' +
                    'end {0};\n'.format(name))

        with open(os.path.join(path, Package._package_order), 'w+') as f:
            f.write('')

    def scan_children(self):
        import os
        for root, dirs, files in os.walk(self._path):
            for d in dirs:
                self.children = os.path.join(root, d)
            for f in files:
                if f.endswith('.mo'):
                    self.models = os.path.join(root, f)

    def scan_parents(self):
        from pathlib import Path
        import os

        has_parent = True
        p = self.path
        while has_parent:
            par = os.path.realpath(Path(p).parent)
            if os.path.exists(os.path.join(par, Package._package_file)):
                has_parent = True
                self.parents = par
                p = par
            else:
                has_parent = False
                self._adam = p

    def add_subpackage(self, sub_pck_name, order='last'):
        import os
        sub_pack_path = os.path.join(self.path, sub_pck_name)
        if sub_pack_path in self.children:
            Warning('Subpackage already existing. Did nothing.')
        else:
            if os.path.exists(sub_pack_path):
                if os.path.isfile(os.path.join(sub_pack_path, self._package_file)) and \
                        os.path.isfile(os.path.join(sub_pack_path, self._package_order)):
                    Warning('Subpackage already existing. Did nothing.')
                else:
                    Package.create_package(sub_pack_path)

            else:
                os.mkdir(sub_pack_path)
                Package.create_package(sub_pack_path)

            self.children = sub_pack_path
            if order == 'last':
                with open(self._order_file, 'a+') as f:
                    f.write(sub_pck_name + '\n')
            elif order == 'first':
                with open(self._order_file, 'r+') as f:
                    content = f.readlines()
                    f.seek(0, 0)
                    f.writelines([sub_pck_name+'\n'] + content)
        self.scan_children()

    def rm_subpackage(self, sub_pck_name):
        import os
        sub_pack_path = os.path.join(self.path, sub_pck_name)
        try:
            os.remove(os.path.join(sub_pack_path, self._package_file))
            os.remove(os.path.join(sub_pack_path, self._package_order))
        except Exception as e:
            raise e

        try:
            if not os.listdir(sub_pack_path):
                os.rmdir(sub_pack_path)
        except FileNotFoundError:
            pass

        try:
            self._childs.remove(sub_pack_path)
        except ValueError:
            pass

        with open(self._order_file, 'r') as f:
            lines = f.readlines()
            newlines = [l for l in lines if l != sub_pck_name + '\n']
        os.remove(self._order_file)
        with open(self._order_file + '_tmp', 'w') as f2:
            f2.writelines(newlines)
        os.rename(self._order_file + '_tmp', self._order_file)

    def get_subpackage(self, sub_pck_path):
        if sub_pck_path in self.child:
            pass

    @property
    def package_file(self):
        return self._package_file


if __name__ == "__main__":
    import os

    genknet = Package("C:/Users/vincent/Documents/Dymola/GenkNET/GenkNET")
    neigh = Package(r'C:\Users\vincent\Documents\Dymola\GenkNET\GenkNET\CoSimulation\Components\Neighborhoud')
    print('end')
