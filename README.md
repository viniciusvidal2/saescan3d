# SAEscan 3D #

## Configuration ##
Use o Visual Studio 2017 ou mais novo e o CMake >= 3.14.

Bibliotecas  
1 - wxWidgest >= 3.1.2 - Você compila ele executando o projeto wx_vcXX.sln (XX é a sua versão do Visual Studio) que está na pasta "wxWidgets-3.1.2\build\msw".  
2 - Eigen >= 3.3 - Usado para manipular as matrizes.  
3 - NSIS >= 3.04 - Usado para criar o instalador.  

Dependências  
1 - installers - Baixe o .7z da seção Downloads do BitBucket e extraia ele na raiz da pasta do DroneManager (no mesmo nível do CMakeLists.txt).  
2 - dependencies - Baixe o .7z da seção Downloads do BitBucket e extraia ele na raiz da pasta do DroneManager (no mesmo nível do CMakeLists.txt).  

## Installing ##

Se você não deseja compilar o projeto, basta executar o instalador disponível no seção Downloads do BitBucket.  

## Creating the installer ##

Depois de criar o projeto do Visual Studio com o CMake, abra o projeto e compile o projeto "PACKAGE".  