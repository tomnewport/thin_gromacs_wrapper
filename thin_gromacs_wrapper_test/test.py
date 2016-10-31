import os
import shutil
import sys
sys.path.append(".")
from thin_gromacs_wrapper import Gromacs, gmx_verbose_handler
"""
if os.path.exists("test_workdir"):
    shutil.rmtree("test_workdir")

os.makedirs("test_workdir")

shutil.copyfile(
    "thin_gromacs_wrapper_test/source_data/1aki.pdb",
    "test_workdir/1AKI.pdb"
    )

shutil.copyfile(
    "thin_gromacs_wrapper_test/source_data/ions.mdp",
    "test_workdir/ions.mdp"
    )

shutil.copyfile(
    "thin_gromacs_wrapper_test/source_data/minim.mdp",
    "test_workdir/minim.mdp"
    )

shutil.copyfile(
    "thin_gromacs_wrapper_test/source_data/nvt.mdp",
    "test_workdir/nvt.mdp"
    )

shutil.copyfile(
    "thin_gromacs_wrapper_test/source_data/npt.mdp",
    "test_workdir/npt.mdp"
    )

shutil.copyfile(
    "thin_gromacs_wrapper_test/source_data/npt.mdp",
    "test_workdir/md.mdp"
    )
"""
gmx = Gromacs()

gmx.cd("test_workdir")
"""
# gmx pdb2gmx -f 1AKI.pdb -o 1AKI_processed.gro -water spce

gmx.pdb2gmx(
    f="1AKI.pdb",
    o="1AKI_processed.gro",
    water="spce"
    ).respond(
        "Select the Force Field:",
        1
    ).call()

# gmx editconf -f 1AKI_processed.gro -o 1AKI_newbox.gro -c -d 1.0 -bt cubic

gmx.editconf(
    f="1AKI_processed.gro",
    o="1AKI_newbox.gro",
    c=True,
    d=1.0,
    bt="cubic"
).call()

# gmx solvate -cp 1AKI_newbox.gro -cs spc216.gro -o 1AKI_solv.gro -p topol.top

gmx.solvate(
    cp="1AKI_newbox.gro",
    cs="spc216.gro",
    o="1AKI_solv.gro",
    p="topol.top"
).call()

# gmx grompp -f ions.mdp -c 1AKI_solv.gro -p topol.top -o ions.tpr

gmx.grompp(
    f="ions.mdp",
    c="1AKI_solv.gro",
    p="topol.top",
    o="ions.tpr"
).call()

# gmx genion -s ions.tpr -o 1AKI_solv_ions.gro -p topol.top -pname NA -nname CL -nn 8

gmx.genion(
    s="ions.tpr",
    o="1AKI_solv_ions.gro",
    p="topol.top",
    pname="NA",
    nname="CL",
    nn=8
).respond(
    "Select a continuous group of solvent molecules",
    "SOL"
    ).call()

# gmx grompp -f minim.mdp -c 1AKI_solv_ions.gro -p topol.top -o em.tpr

gmx.grompp(
    f="minim.mdp",
    c="1AKI_solv_ions.gro",
    p="topol.top",
    o="em.tpr"
    ).call()

# gmx mdrun -v -deffnm em

gmx.mdrun(
   deffnm="em",
   v=True
).call(
    timeout=360,
    handler=gmx_verbose_handler
    )

# gmx grompp -f nvt.mdp -c em.gro -p topol.top -o nvt.tpr

gmx.grompp(
    f="nvt.mdp",
    c="em.gro",
    p="topol.top",
    o="nvt.tpr"
).call()
"""
# gmx mdrun -deffnm nvt

gmx.mdrun(
   deffnm="nvt",
   v=True
).call(
    timeout=360,
    handler=gmx_verbose_handler
    )

# gmx grompp -f npt.mdp -c nvt.gro -t nvt.cpt -p topol.top -o npt.tpr

gmx.grompp(
    f="npt.mdp",
    c="nvt.gro",
    t="nvt.cpt",
    p="topol.top",
    o="npt.tpr"
).call()

# gmx mdrun -deffnm npt

gmx.mdrun(
   deffnm="npt",
   v=True
).call(
    timeout=360,
    handler=gmx_verbose_handler
    )

# gmx grompp -f md.mdp -c npt.gro -t npt.cpt -p topol.top -o md_0_1.tpr

gmx.grompp(
    f="md.mdp",
    c="npt.gro",
    t="npt.cpt",
    p="topol.top",
    o="md_0_1.tpr"
).call()

# gmx mdrun -deffnm md_0_1
gmx.mdrun(
   deffnm="md_0_1",
   v=True
).call(
    timeout=360,
    handler=gmx_verbose_handler
    )
