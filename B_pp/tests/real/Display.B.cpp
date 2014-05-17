@@GUIDE
@Passes = 5

@@TEMPLATE
// This is the front half of the pt correlation code

#define BUFSIZE 32768

// Includes
#include <iostream>
#include <stdlib.h>
#include <stdio.h>
#include <string>
#include <math.h>
#include <algorithm> //required for std::swap
#include <output.h>
#include <efficiency.h>
#include <sys/stat.h>

using namespace std;

// Prototypes
void trackanalysisfunction(void);
void LoadFiles(void);
void LoadCuts(void);
bool CheckTrack(void);

// Globals
bool Good_Tracks;
int goodMult;
int refMult;
int totalNumberOfevents;
string directory;
const char *Headers[@numFiles@];
const char *Events[@numFiles@];

int Total[2000];
int Count[2000];

FILE *fp;
FILE *fh;
int iFile;
int myLocal;
int eventNumber;
int myDisplay;
bool eventCut;
bool etaCut;
bool ptCut;
// Header information
@HeaderMetaData.type@ @HeaderMetaData.name@;
// Event information
@EventMetaData.type@ @EventMetaData.name@;
// Analysis Cuts
double @AnalysisCuts.name@_cut[2];
// Command Line Cuts
double @EventMetaData.name@_Ccut[3];
double @HeaderMetaData.name@_Ccut[3];

int main(int argc, char* argv[]){
    cout << "Welcome to Display program" << endl;
    directory = "Output/";

    LoadFiles();

    for(int i=0; i<2000; i++){
        Total[i] = 0;
        Count[i] = 0;
    }

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Loading cuts from file" << endl;
    LoadCuts();

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Loading command line cuts" << endl;
    int i = 1;
    while(i != argc){
        if(strcmp(argv[i],"directory")==0){
            directory=argv[i+1];
            i+=2;
            cout << i << endl; cout.flush();
        } else if(strcmp(argv[i],"@HeaderMetaData.name@")==0) { @HeaderMetaData.name@_Ccut[0] = atof(argv[i+1]); @HeaderMetaData.name@_Ccut[1] = atof(argv[i+2]); @HeaderMetaData.name@_Ccut[2] = 1; i+=3;
        } else if(strcmp(argv[i],"@EventMetaData.name@")==0) { @EventMetaData.name@_Ccut[0] = atof(argv[i+1]); @EventMetaData.name@_Ccut[1] = atof(argv[i+2]); @EventMetaData.name@_Ccut[2] = 1; i+=3;
        }
    }
    string command = "mkdir -p " + directory + "/";
    system(command.c_str());

    totalNumberOfevents = 0;
    myDisplay = 10000;

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Starting Analysis" << endl;


	for(iFile=0;iFile<@numFiles@;iFile++){
		cout << "Begin file " << iFile+1 << ", " << Events[iFile] << endl;
        	char dBuffer[BUFSIZE];
		fh=fopen(Events[iFile],"rb");
        	//setbuf( fh, dBuffer );
		fread(&goodMult,sizeof(int),1,fh);	
		while(!feof(fh)){
			fread(&@HeaderMetaData.name@,sizeof(@HeaderMetaData.type@),1,fh);
			myLocal++;
			totalNumberOfevents++;
			if(myLocal == myDisplay){
				cout << "Event " << totalNumberOfevents << " for file " << iFile+1 << " of " << @numFiles@ << endl; cout.flush();
				myLocal=0;
			}
			for(int iEvent=0;iEvent<goodMult;iEvent++){
				fread(&@EventMetaData.name@,sizeof(@EventMetaData.type@),1,fh);
				trackanalysisfunction();
			}
			fread(&goodMult,sizeof(int),1,fh);	
		}
		fclose(fh);
		cout << "Events read from file " << Events[iFile] << " giving " << totalNumberOfevents << endl;
	}
	cout << "Total number of events read = " << totalNumberOfevents << endl;

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Analysis Finished. Creating Output" << endl;

    fstream Efficiency;
    string fname = directory+"/Efficiency_vs_pt.txt";
    Efficiency.open(fname.c_str(), fstream::out );
    for(int i=0; i<2000; i++){
        if(Total[i] != 0){
            Efficiency << float(i)/1000 << " " << float(Count[i])/float(Total[i]) << endl;
        } else {
            Efficiency << float(i)/1000 << " 0" << endl;
        }
    }

    return 0;
}

void trackanalysisfunction(void){
        //cout << pid << " " ; cout.flush();
	if(CheckTrack()){
                Total[int(pt*1000)] += 1;
                if( eff( pid, pt, eta, phi, 0) > (float(rand()%1000000)/1000000) ){
                          Count[int(pt*1000)] += 1;
                }
        }
}

void LoadFiles(void){
    Events[@i@] = "@EventFiles.name@";
}

void LoadCuts(void){
    @AnalysisCuts.name@_cut[0] = @AnalysisCuts.low@;
    @AnalysisCuts.name@_cut[1] = @AnalysisCuts.high@;
    @EventMetaData.name@_Ccut[2] = 0;
    @HeaderMetaData.name@_Ccut[2] = 0;
}

bool CheckTrack(void){
    bool good = true;
    if((@AnalysisCuts.name@ < @AnalysisCuts.name@_cut[0]) || (@AnalysisCuts.name@ > @AnalysisCuts.name@_cut[1])) good = false;
    if((@HeaderMetaData.name@_Ccut[2] == 1) && ((@HeaderMetaData.name@ < @HeaderMetaData.name@_Ccut[0]) || (@HeaderMetaData.name@ > @HeaderMetaData.name@_Ccut[1]))) good = false;
    if((@EventMetaData.name@_Ccut[2] == 1) && ((@EventMetaData.name@ < @EventMetaData.name@_Ccut[0]) || (@EventMetaData.name@ > @EventMetaData.name@_Ccut[1]))) good = false;
    return good;
}

@@ITERABLES
@HeaderFiles(name):
%good_runs_final.txt[4,:,2]%
@EventFiles(name):
%good_runs_final.txt[3,:,2]%
@HeaderMetaData(name,type):
%%good_runs_final.txt[2]%%
@EventMetaData(name,type):
%%good_runs_final.txt[1]%%
@AnalysisCuts(name,low,high):
%analysisCuts.txt[1,:]%

@@FORMS
@Read(name,type,file):
fread(&[name],sizeof([type]),1,[file]);

@@REFERENCES
@numFiles:
%good_runs_final.txt[0]%
