"""
Model exported as python.
Name : modelo
Group : 
With QGIS : 32202
"""

from qgis.core import QgsProcessing,NULL
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingUtils
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsCoordinateReferenceSystem
import processing
from math import sin, cos, sqrt, radians,tan,pow,pi


class Modelo(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('ponto', 'ponto', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('campo', 'Campo (Escolha se não for usar uma altitude média)', optional=True, type=QgsProcessingParameterField.Numeric, parentLayerParameterName='ponto', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterBoolean('desejausarumaaltitude', 'Deseja usar uma altitude ', defaultValue=False))
        self.addParameter(QgsProcessingParameterNumber('valoraltitudemedia', 'Valor de altitude média (0 se for usar uma coluna para cálculo)', optional=True, type=QgsProcessingParameterNumber.Double, minValue=-1.79769e+308, maxValue=1.79769e+308, defaultValue=0))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # Gerar exceçãoam
        if parameters['campo'] == NULL and parameters['desejausarumaaltitude']== False:
            
            alg_params = {
            'CONDITION': '1 = 1',
            'MESSAGE': 'Escolha uma opção: defina a altitude média ou o campo com as altitudes'
            }
            outputs['GerarExceo'] = processing.run('native:raiseexception', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        #print(parameters['campo'])
        #print(parameters['desejausarumaaltitude'])
        if parameters['campo'] == NULL and parameters['desejausarumaaltitude']== True and parameters['valoraltitudemedia'] <=0.000000:
        # Gerar exceção
            
           
            alg_params = {
                'CONDITION': '1 = 1 ',
                'MESSAGE': 'Defina uma altitude média ou desmarque a opção e defina o campo das altitudes'
            }
            outputs['GerarExceo'] = processing.run('native:raiseexception', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': parameters['ponto'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4674'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        
        outputs['ReprojetarCamada'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        layer = QgsProcessingUtils.mapLayerFromString(outputs['ReprojetarCamada']['OUTPUT'],context)
        lat=[]
        lon=[]
        lat1=[]
        lon1=[]
        h=[]
        a= 6378137
        f=1/298.257222101
        e2= f*(2-f)
        
        for feature in layer.getFeatures():
            
            if parameters['campo'] != NULL:
                
                idx = layer.fields().indexFromName(parameters['campo'])
                h.append(float(feature.attributes()[idx]))
                
            else:
                print(parameters['valoraltitudemedia'])
                h.append(parameters['valoraltitudemedia'])
                
            lon1.append(feature.geometry().get().x())
            lat1.append(feature.geometry().get().y())
            

        d=coordenadas_Sirgas(lon1,lat1,h,a,e2)
        
        results['area_sistema_topografico_local']=d.area_gauss(1)
        results['latitude']=d.la0
        results['longitude']=d.lo0
        results['h0']=d.ha0
        
        
        return results

    def name(self):
        return 'modelo'

    def displayName(self):
        return 'modelo'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Modelo()

class coordenadas_Sirgas:
    
    """ classe das coordenadas utm 
    É instaciada com o seguintes atributos:
     E_list: array das coordenadas longitude em  graus decimais; 
     N_list: array das coordenadas latitude em graus decimais;
     h_list: altitude elipsoidal;
     #zone: zona UTM ex. '22S';
     a: semi-eixo maior em metros ex. 6378137;
     f: fator de flattening ex. 1/298.257223563;
     """

    def __init__(self,E_list,N_list,h_list,a,e2):
      

        self.E_list=E_list
        self.N_list=N_list
        self.h_list=h_list
        self.a=a 
        self.e2=e2
        self.la0=0
        self.lo0=0
        self.ha0=0
       
    def trans_geodesicas2cartesianas(self):
        """ função que converte coordenadas geodesicas para cartesianas geocentricas
        parametros:
        lat: latitude em graus decimais
        lon: longitude em graus decimais
        hi: altura em metros
        a: semi-eixo do elipsoide
        f: fator de achatamento
        output:
        """        
        a= self.a
        e2= self.e2
        hi=self.h_list
        lat=self.N_list
        lon=self.E_list        
        cont = 0
        Xi=[]
        Yi=[]
        Zi=[]
        
        while cont<len(lat):
        
            la=(lat[cont]*pi/180)
            lo=(lon[cont]*pi/180)
            Ni= a/(1-e2*sin(la)**2)**0.5
            X= (Ni+hi[cont])*cos(la)*cos(lo)
            Y= (Ni+hi[cont])*cos(la)*sin(lo)
            Z= (Ni*(1-e2)+hi[cont])*sin(la)           
            Xi.append(X)
            Yi.append(Y)
            Zi.append(Z)
            cont+=1

        return Xi,Yi,Zi
        
    def origem_stl(self):

      e0=[sum(self.E_list)/len(self.E_list)]
      n0=[sum(self.N_list)/len(self.N_list)]
      h0=[sum(self.h_list)/len(self.h_list)]
      self.la0=n0
      self.lo0=e0
      self.ha0=h0
      origem = coordenadas_Sirgas(e0,n0,h0,self.a,self.e2)
      x0,y0,z0= origem.trans_geodesicas2cartesianas()
      
      return n0[0],e0[0],x0[0],y0[0],z0[0]

    def transf_carte2local(self):
        
      fi0,lam0,x0,y0,z0=self.origem_stl()
      fi0,lam0=fi0*pi/180,lam0*pi/180
      xi,yi,zi = self.trans_geodesicas2cartesianas()
      ei=[]
      ni=[]
      ui=[]
      
      for j in range(len(xi)):     
          
        ei.append(-sin(lam0)*(xi[j]-x0)+cos(lam0)*(yi[j]-y0))
        ni.append(-sin(fi0)*cos(lam0)*(xi[j]-x0)-sin(fi0)*sin(lam0)*(yi[j]-y0)+cos(fi0)*(zi[j]-z0))
        ui.append(cos(fi0)*cos(lam0)*(xi[j]-x0)+cos(fi0)*sin(lam0)*(yi[j]-y0)+sin(fi0)*(zi[j]-z0))      
        
      return ei,ni,ui

    def area_gauss(self,t):
        
      e =[]
      n=[]
      u=[]
      if len(self.N_list)>3:
          
        if t ==1:
            
          e,n,u =  self.transf_carte2local()          
                
        elif t ==2:
          e = self.E_list
          n = self.N_list
        
        elif t ==3:
          e,n,u = self.trans_geodesicas2cartesianas()
        
        len_n= len(n)
        cont=0       
        sum1=0
        sum2=0
        
        while cont<len_n:
            
          sum1+=n[cont]*e[cont-1]
          sum2+=e[cont]*n[cont-1]  
          cont+=1
      
        return (abs(sum2-sum1)/2)
      else:
        return 0



