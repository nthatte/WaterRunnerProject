all: cpg-crop.pdf cpg.pdf schematic-crop.pdf schematic.pdf foot_traj_orig.eps foot_traj_simple.eps wheuristic.pdf woheuristic.pdf robot.JPG boom.jpg basilisk-lizard.jpg

cpg-crop.pdf : cpg.pdf
	pdfcrop cpg.pdf

cpg.pdf : cpg.tikz cpg.tex ../mycolors.tex
	xelatex cpg.tex

schematic-crop.pdf : schematic.pdf
	pdfcrop schematic.pdf

schematic.pdf : schematic.tikz schematic.tex ../mycolors.tex
	xelatex schematic.tex

foot_traj_orig.eps : foot_traj_orig.graffle leg.pdf legspeed.pdf
	./graffle.sh foot_traj_orig.graffle foot_traj_orig.eps

foot_traj_simple.eps : foot_traj_simple.graffle leg2.pdf leg2speed.pdf
	./graffle.sh foot_traj_simple.graffle foot_traj_simple.eps

leg.pdf legspeed.pdf leg2.pdf leg2speed.pdf : traj.py matplotlibrc
	python traj.py

wheuristic.pdf woheuristic.pdf : results.py data1.mat matplotlibrc
	python results.py

.PHONY: robot.JPG boom.jpg basilisk-lizard.jpg
