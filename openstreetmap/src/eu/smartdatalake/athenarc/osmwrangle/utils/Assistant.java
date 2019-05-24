/*
 * @(#) Assistant.java 	 version 1.8  2/5/2019
 *
 * Copyright (C) 2013-2019 Information Management Systems Institute, Athena R.C., Greece.
 *
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package eu.smartdatalake.athenarc.osmwrangle.utils;

import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.nio.charset.Charset;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TimeZone;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;

import org.apache.commons.io.FilenameUtils;
import org.geotools.geometry.jts.JTS;
import org.geotools.referencing.CRS;
import org.opengis.geometry.MismatchedDimensionException;
import org.opengis.referencing.FactoryException;
import org.opengis.referencing.crs.CoordinateReferenceSystem;
import org.opengis.referencing.operation.MathTransform;
import org.opengis.referencing.operation.TransformException;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vividsolutions.jts.geom.Envelope;
import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.LineString;
import com.vividsolutions.jts.geom.LinearRing;
import com.vividsolutions.jts.geom.MultiPolygon;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.Polygon;
import com.vividsolutions.jts.io.WKTReader;
import com.vividsolutions.jts.io.WKTWriter;
import com.vividsolutions.jts.operation.polygonize.Polygonizer;


/**
 * Assistance class with various helper methods used in transformation or reverse transformation.
 * @author Kostas Patroumpas
 * @version 1.8
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 9/3/2013
 * Modified: 15/12/2017, included support for extra geometric transformations 
 * Modified: 9/2/2018, included additional execution statistics
 * Modified: 23/4/2018, added support for executing build-in functions at runtime using the Java Reflection API.
 * Modified: 30/4/2018; calculation of area and length for geometries done in Cartesian coordinates in order to return values in SI units (meters, square meters)
 * Modified: 27/7/2018; auto-generation of intermediate identifiers if missing in the original data
 * Modified: 27/7/2018; added function to validate ISO 639-1 language codes
 * Modified: 9/10/2018; added built-in function to generate URIs based either on UUIDs or original feature IDs
 * Modified: 7/11/2018; added built-in function to support transliteration of string literals into Latin
 * Modified: 26/11/2018; added built-in function for formatting phone numbers
 * Modified: 18/4/2019; added support for topological filtering of geometries; currently based on spatial containment in a user-specified geometry
 * Last modified by: Kostas Patroumpas, 2/5/2019
 */

public class Assistant {

	public WKTReader wktReader = null;             //Parses a geometry in Well-Known Text format to a Geometry representation.
	
	private static Envelope mbr;                   //Minimum Bounding Rectangle (in WGS84) of all geometries handled during a given transformation process
	private static Configuration currentConfig;

	private static Set<String> ISO_LANGUAGES = new HashSet<String> (Arrays.asList(Locale.getISOLanguages()));   //List of ISO 639-1 language codes
	
	private AtomicLong numberGenerator = new AtomicLong(1L);    //Used to generate serial numbers, i.e., consecutive positive integers starting from 1
	 
	/**
	 * Constructor of the class without explicit declaration of configuration settings.
	 */
	public Assistant() {		
	}
	
	/**
	 * Constructor of the class with explicit declaration of configuration settings.
	 */
	public Assistant(Configuration config) {
		
		currentConfig = config;

	}  

	/**
	 * Examines whether a given string is null or empty (blank).		
	 * @param text  The input string
	 * @return  True if the parameter is null or empty; otherwise, False.
	 */
	public boolean isNullOrEmpty(String text) {
		
	    if (text == null || text.equals("")) {
	      return true;
	    } else {
	      return false;
	    }
		  
	}


	
	/**
	 * Returns a String with the content of the InputStream	
	 * @param is  the InputStream.
	 * @return  A string with the content of the InputStream.
	 * @throws IOException
	 */
	public String convertInputStreamToString(InputStream is) throws IOException {
		
	    if (is != null) {
	      StringBuilder sb = new StringBuilder();
	      String line;
	      try {
	        BufferedReader reader = new BufferedReader(new InputStreamReader(is, Constants.UTF_8));
	        while ((line = reader.readLine()) != null) {
	          sb.append(line).append(Constants.LINE_SEPARATOR);
	        }
	      } finally {
	        is.close();
	      }
	      return sb.toString();
	    } else {
	      return "";
	    }	  
	}


	/**
	 * Returns an InputStream with the content of the given string.
	 * @param string  A string to be converted.
	 * @return InputStream with the string value.
	 */
	public InputStream convertStringToInputStream(String string) {
		
	    InputStream is = null;
	    try {
	      is = new ByteArrayInputStream(string.getBytes("UTF-8"));
	    } catch (UnsupportedEncodingException e) {
	      e.printStackTrace();
	    }
	    return is;	  
	}

	/**
	 * Get the current time (in the GMT time zone) to be used in user notifications.	
	 * @return  A timestamp value as string.
	 */
	public String getGMTime() {
		
		SimpleDateFormat gmtDateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS");
		gmtDateFormat.setTimeZone(TimeZone.getTimeZone("GMT"));

		//Current Date Time in GMT
		return gmtDateFormat.format(new java.util.Date()) + " GMT";		
	}

	/**
	 * Notifies the user about progress in parsing input records.	
	 * @param numRec  The number of records processed so far.
	 */
	public void notifyProgress(int numRec) {
			
		if (numRec % 1000 == 0)
		    System.out.print(this.getGMTime() + " " + Thread.currentThread().getName() + " Processed " +  numRec + " entities..." + "\r");
	}


	
	
	/**
	 * Report statistics upon termination of the transformation process.
	 * @param dt  The clock time (in milliseconds) elapsed since the start of transformation process.
	 * @param numRec  The total number of input records that have been processed.
	 * @param rejectedRec  The total number of input records that were rejected during processing.
	 * @param numTriples  The number of RDF triples resulted from transformation.
	 * @param serialization  A string with the user-specified serialization of output triples.
	 * @param mode  Transformation mode, as specified in the configuration.
	 * @param targetSRID  Output spatial reference system (CRS).
	 * @param outputFile  Path to the output file containing the RDF triples.
	 */
	public void reportStatistics(long dt, int numRec, int rejectedRec, String targetSRID, String outputFile) {

		System.out.print(this.getGMTime() + " Thread " + Thread.currentThread().getName() + " completed successfully in " + dt + " ms. " + (numRec-rejectedRec) + " entities transformed and exported to file: " + outputFile + ".");
	
		if (rejectedRec > 0)
			System.out.print(" " + rejectedRec + " input entities were excluded from transformation.");
		System.out.println();
		
		 if (mbr != null)
			 System.out.println("MBR of transformed geometries: X_min=" + mbr.getMinX() + ", Y_min=" + mbr.getMinY() + ", X_max=" + mbr.getMaxX() + ", Y_max=" + mbr.getMaxY());
		 
		 //Metadata regarding execution of this process
		 Map<String, Object> execStatistics = new HashMap<String, Object>();
		 execStatistics.put("Execution time (ms)", dt);
		 execStatistics.put("Input entities count", numRec);
		 execStatistics.put("Input entities transformed", numRec-rejectedRec);
		 execStatistics.put("Input entities excluded", rejectedRec);
		 if (targetSRID != null)
			 execStatistics.put("Output CRS", "EPSG:" + targetSRID);
		 else
			 execStatistics.put("Output CRS", "EPSG:4326");             //Assuming default CRS: WGS84
		 execStatistics.put("Output file", outputFile);
	
		 //MBR of transformed geometries
		 Map<String, Object> mapMBR = new HashMap<String, Object>();
		 if (mbr != null) {
			 mapMBR.put("X_min", mbr.getMinX());
			 mapMBR.put("Y_min", mbr.getMinY());
			 mapMBR.put("X_max", mbr.getMaxX());
			 mapMBR.put("Y_max", mbr.getMaxY());
		 }
		
		 //Compile all metadata together
		 Map<String, Object> allStats = new HashMap<String, Object>();
		 allStats.put("Execution Metadata", execStatistics);
		 allStats.put("MBR of transformed geometries (WGS84)", mapMBR);
 
	    //Convert metadata to JSON and write to a file
	    try {
	    	ObjectMapper mapper = new ObjectMapper();
	        mapper.writeValue(new File(FilenameUtils.removeExtension(outputFile) + "_metadata.json"), allStats);
	    } catch (Exception e) {
	        e.printStackTrace();
	    }	
	}

	/**
	 * Removes a given directory and all its contents. Used for removing intermediate files created during transformation.	
	 * @param path The path to the directory.
	 * @return  The path to a temporary directory that holds intermediate files.
	 * @throws IOException 
	 */
	public String removeDirectory(String path){

	      File f = new File(path);

	      if (f.isDirectory()) {
	        if (f.exists()) {
	          String[] myfiles = f.list();
	          if (myfiles.length > 0) {
	            for (int i = 0; i < myfiles.length; i++) {
	              File auxFile = new File(path + "/" + myfiles[i]);     //Always safe to use '/' instead of File.separatorChar in any OS
//				  System.out.println("Removing ... " + auxFile.getPath());
	              if (auxFile.isDirectory())      //Recursively delete files in subdirectory
	            	  removeDirectory(auxFile.getPath());
	              auxFile.delete();
	            }
	          }
	          f.delete();
	        }
	      }

	      return path;	
	}

	/**
	 * Removes all files from a given directory. Used for removing intermediate files created during transformation.	
	 * @param path The path to the directory.
	 * @throws IOException 
	 */
	public void cleanupFilesInDir(String path){
		 
		File f = new File(path);

	      if (f.isDirectory()) {
	        if (f.exists()) {
	          String[] myfiles = f.list();
	          if (myfiles.length > 0) {
	            for (int i = 0; i < myfiles.length; i++) {
	              File auxFile = new File(path + "/" + myfiles[i]);     //Always safe to use '/' instead of File.separatorChar in any OS
//				  System.out.println("Removing ... " + auxFile.getPath());
	              if (auxFile.isDirectory())      //Recursively delete files in subdirectory
	            	  removeDirectory(auxFile.getPath());
	              auxFile.delete();
	            }
	          }
	        }
	      }
	}
	
	/**
	 * Creates a temporary directory under the specified path. Used for holding intermediate files created during transformation.	
	 * @param path The path to the directory.
	 * @return  The path to a temporary directory that holds intermediate files.
	 */
	public String createDirectory(String path) {
		
		String dir = path;

		if ((path.charAt(path.length()-1)!=File.separatorChar) && (path.charAt(path.length()-1)!= '/'))
	        dir = path + "/";         //Always safe to use '/' instead of File.separatorChar in any OS

	      File f = new File(dir);

	      if (!f.isDirectory()) {
	        f.mkdir();
	      }

	      dir = dir + UUID.randomUUID() + "/";    //Generate a subdirectory that will be used for thread-safe graph storage when multiple threads are employed	      
	      
	      File fl = new File(dir);	      
		  fl.mkdir();
		  
	      return dir;	
	}


 
	/**
	 * Updates the MBR of the geographic dataset as this is being transformed. 	
	 * @param g  Geometry that will be checked for possible expansion of the MBR of all features processed thus far
	 */
	public void updateMBR(Geometry g) {
			
		Envelope env = g.getEnvelopeInternal();          //MBR of the given geometry
		if (mbr == null)
			mbr = g.getEnvelopeInternal();
		else if (!mbr.contains(env))
			mbr.expandToInclude(env);                    //Expand MBR is the given geometry does not fit in
	}
		

	/**
	 * Transforms a WKT representation of a geometry into another CRS (reprojection).	
	 * @param wkt  Input geometry in Well-Known Text.
	 * @param transform  Parameters for the transformation, including source and target CRS.
	 * @return  WKT of the transformed geometry.
	 */
	public String wktTransform(String wkt, MathTransform transform) {  
	  	      
	   Geometry o = null;
       //Apply transformation
        try {
        	o = wktReader.read(wkt);
        	o = JTS.transform(o, transform);

        	//Update the MBR of all geometries processed so far
  	        //updateMBR(o);
		} catch (Exception e) {
			e.printStackTrace();
		}
         
        return o.toText();     //Get transformed WKT representation	
	}
	
	/** 
	 * Transforms an original geometry into another CRS (reprojection).
	 * @param g  Input geometry
	 * @param transform   Parameters for the transformation, including source and target CRS
	 * @return the transformed geometry
	 */
	public Geometry geomTransform(Geometry g, MathTransform transform) {  
	  	     
       //Apply transformation
        try {
        	g = JTS.transform(g, transform);
		} catch (Exception e) {
			e.printStackTrace();
		}
        
        return g;     //Return transformed geometry
	}

	/**
	 * Reprojects a given geometry into the WGS84 (lon/lat) coordinate reference system
	 * @param wkt  Well-Known Text of the input geometry
	 * @param srid  EPSG code of the coordinate reference system (CRS) of the geometry
	 * @return  Geometry reprojected into WG84 system
	 */
	public Geometry geomTransformWGS84(String wkt, int srid) {
		
	    WKTReader wktReader = new WKTReader();
	    Geometry g = null;
        try {
        	g = wktReader.read(wkt);
        	if (srid != 4326)                   //In case that geometry is NOT georeferenced in WGS84, ...
        	{                                   //... it should be transformed in order to calculate its lon/lat coordinates
        		CoordinateReferenceSystem origCRS = CRS.decode("EPSG:" + srid);    //The CRS system of the original geometry
        		CoordinateReferenceSystem finalCRS = CRS.decode("EPSG:4326");      //CRS for WGS84
        		//Define a MathTransform object and apply it
        		MathTransform transform = CRS.findMathTransform(origCRS, finalCRS);
        		g = JTS.transform(g, transform); 	        		
        	}
        }
        catch (Exception e) {
				e.printStackTrace();
			}
        
        return g;
	}
	
	/**
	 * Projects the given geometry to a flat Cartesian plane
	 * @param g  Input geometry
	 * @param srid  EPSG code of the coordinate reference system (CRS) of the geometry
	 * @return  Projected geometry to a flat Cartesian plane
	 */
	public Geometry geomFlatTransform(Geometry g, int srid) {
		
		Point centroid = g.getCentroid();
	    try {	    	
	      //Convert geometry to a flat Cartesian plane using GeoTools auto projection (assuming the shape is small enough to minimize error)
	      String code = "AUTO2:42001," + centroid.getX() + "," + centroid.getY();
	      CoordinateReferenceSystem auto = CRS.decode(code, true);
//	      System.out.println("Coordinate system units: " + auto.getCoordinateSystem().getAxis(0).getUnit().toString());
	  	
	      CoordinateReferenceSystem targetCRS = CRS.decode("EPSG:" + srid);  
	      MathTransform transform = CRS.findMathTransform(targetCRS, auto);
	      Geometry gProjected = JTS.transform(g, transform);      
      
	      return gProjected;		                    //Projected geometry
	    } 
	    catch (MismatchedDimensionException | TransformException | FactoryException e) { e.printStackTrace(); }
	    
	    return null;
	}
	
		
	/**
	 * Get / create a valid version of the geometry given. If the geometry is a polygon or multi polygon, self intersections /
	 * inconsistencies are fixed. Otherwise the geometry is returned.
	 * 
	 * @param geom
	 * @return a geometry 
	 */
	@SuppressWarnings("unchecked")
	public Geometry geomValidate(Geometry geom){
	    if(geom instanceof Polygon){
	        if(geom.isValid()){
	            geom.normalize(); // validate does not pick up rings in the wrong order - this will fix that
	            return geom; // If the polygon is valid just return it
	        }
	        Polygonizer polygonizer = new Polygonizer();
	        addPolygon((Polygon)geom, polygonizer);
	        return toPolygonGeometry(polygonizer.getPolygons(), geom.getFactory());
	    }else if(geom instanceof MultiPolygon){
	        if(geom.isValid()){
	            geom.normalize(); // validate does not pick up rings in the wrong order - this will fix that
	            return geom; // If the multipolygon is valid just return it
	        }
	        Polygonizer polygonizer = new Polygonizer();
	        for(int n = geom.getNumGeometries(); n-- > 0;){
	            addPolygon((Polygon)geom.getGeometryN(n), polygonizer);
	        }
	        return toPolygonGeometry(polygonizer.getPolygons(), geom.getFactory());
	    }else{
	        return geom; // In my case, I only care about polygon / multipolygon geometries
	    }
	}

	/**
	 * Add all line strings from the polygon given to the polygonizer
	 * 
	 * @param polygon Polygon from which to extract line strings
	 * @param polygonizer Polygonizer object
	 */
	public void addPolygon(Polygon polygon, Polygonizer polygonizer){
	    addLineString(polygon.getExteriorRing(), polygonizer);
	    for(int n = polygon.getNumInteriorRing(); n-- > 0;){
	        addLineString(polygon.getInteriorRingN(n), polygonizer);
	    }
	}

	/**
	 * Add the linestring given to the polygonizer
	 * 
	 * @param linestring Line string
	 * @param polygonizer Polygonizer object
	 */
	public void addLineString(LineString lineString, Polygonizer polygonizer){

	    if(lineString instanceof LinearRing){ // LinearRings are treated differently to line strings : we need a LineString NOT a LinearRing
	        lineString = lineString.getFactory().createLineString(lineString.getCoordinateSequence());
	    }

	    // unioning the linestring with the point makes any self intersections explicit.
	    Point point = lineString.getFactory().createPoint(lineString.getCoordinateN(0));
	    Geometry toAdd = lineString.union(point); 

	    //Add result to polygonizer
	    polygonizer.add(toAdd);
	}

	/**
	 * Get a geometry from a collection of polygons.
	 * 
	 * @param polygons Collection of polygons
	 * @param factory Factory to generate MultiPolygon if required
	 * @return null if there were no polygons, the polygon if there was only one, or a MultiPolygon containing all polygons otherwise
	 */
	public Geometry toPolygonGeometry(Collection<Polygon> polygons, GeometryFactory factory){
	    switch(polygons.size()){
	        case 0:
	            return null; // No valid polygons!
	        case 1:
	            return polygons.iterator().next(); // single polygon - no need to wrap
	        default:
	            //polygons may still overlap! Need to sym difference them
	            Iterator<Polygon> iter = polygons.iterator();
	            Geometry ret = iter.next();
	            while(iter.hasNext()){
	                ret = ret.symDifference(iter.next());
	            }
	            return ret;
	    }
	}
	
	/** 
	 * Provides the Well-Known Text representation of a geometry for its inclusion as literal in RDF triples.
	 * @param g  Input geometry
	 * $param geomOntology  RDF ontology used in geometry representations (GeoSPARQL, Virtuoso geometry RDF, or WGS84 Geoposition RDF vocabulary)
	 * @return  WKT of the geometry
	 */	
	public String geometry2WKT(Geometry g, String geomOntology) {  
	  	     
	    WKTWriter writer = new WKTWriter();
	    String wkt;

        //Convert geometry into WKT
        if (geomOntology.toLowerCase().equals("geosparql"))
        	wkt = writer.writeFormatted(g);        //GeoSPARQL WKT representation for various types of geometries
        else
        	wkt = g.toText();                      //WKT representation for Virtuoso or WGS84 GeoPosition RDF vocabulary
            
        //Update the MBR of all geometries processed so far
        //updateMBR(g);
      
        return wkt;     //Return transformed geometry in WKT representation
	}	

	/** 
	 * Returns the internal geometry representation according to its Well-Known Text serialization.
	 * @param wkt  WKT of the geometry
	 * @return  A geometry object
	 */
	public Geometry WKT2Geometry(String wkt) {  
	  	    
		WKTReader wktReader = new WKTReader();
		Geometry g = null;
        try {
        	g = wktReader.read(wkt);

        	//Update the MBR of all geometries processed so far
  	        //updateMBR(g);
		} catch (Exception e) {
			e.printStackTrace();
		}
    
        return g;     //Return geometry
	}	
	
	/** 
	 * Returns the area of a polygon geometry from its the Well-Known Text representation.
	 * @param polygonWKT  WKT of the polygon
	 * @return  calculated area (in the same units as the CRS of the geometry)
	 */
	public double getArea(String polygonWKT) {
			
		Geometry g = WKT2Geometry(polygonWKT);
		return g.getArea();		                //Calculate the area of the given (multi)polygon 	
	}
	
	/** 
	 * Built-in function that returns the area of a polygon geometry from its the Well-Known Text representation.
	 * @param polygonWKT  WKT of the polygon
	 * @param targetSRID  EPSG code of the coordinate reference system (CRS) of the geometry
	 * @return  calculated area in square meters (NOT in the units of the CRS of the geometry)
	 */
	public double getArea(String polygonWKT, int targetSRID) {
			
		Geometry g = WKT2Geometry(polygonWKT);
		Geometry gProjected = geomFlatTransform(g, targetSRID);     //Geometry projected to a flat Cartesian plane
		if (gProjected != null)
			return gProjected.getArea();		                    //Calculate the area of the projected (multi)polygon in SQUARE METERS
	    
	    return 0.0;            //This is not a polygon geometry, so it has no area 	
	}

	/** 
	 * Returns the length of a linestring or the perimeter of a polygon geometry from its the Well-Known Text representation.
	 * @param wkt WKT of the linestring or polygon
	 * @return  calculated length/perimeter (in the same units as the CRS of the geometry)
	 */	
	public double getLength(String wkt) {
		
		Geometry g = WKT2Geometry(wkt);
		return g.getLength();		                //Calculate the length of the given (multi)linestring or the perimeter of the given (multi)polygon	
	}
	
	/** 
	 * Built-in function that returns the length of a linestring or the perimeter of a polygon geometry from its the Well-Known Text representation.
	 * @param wkt WKT of the linestring or polygon
	 * @param targetSRID  EPSG code of the coordinate reference system (CRS) of the geometry
	 * @return  calculated length/perimeter in square meters (NOT in the units of the CRS of the geometry)
	 */	
	public double getLength(String wkt, int targetSRID) {
		
		Geometry g = WKT2Geometry(wkt);
		Geometry gProjected = geomFlatTransform(g, targetSRID);     //Geometry projected to a flat Cartesian plane
		if (gProjected != null)
			return gProjected.getLength();	//Calculate the length of the given (multi)linestring or the perimeter of the given (multi)polygon in SQUARE METERS

		return 0.0;   //This is not a line or polygon geometry, so it has no length or perimeter
	}
	
	/** 
	 * Built-in function that returns a pair of lon/lat coordinates (in WGS84) of a geometry as calculated from its the Well-Known Text representation.
	 * @param wkt   WKT of the geometry
	 * @param targetSRID   the EPSG code of the CRS of this geometry 
	 * @return  An array with the pair of lon/lat coordinates
	 */
	public double[] getLonLatCoords(String wkt, int targetSRID) {

	    Geometry g = geomTransformWGS84(wkt, targetSRID);
	    if (g != null)
	    {	
        	//Update the MBR of all geometries processed so far
  	        updateMBR(g);
        	
        	//Calculate the coordinates of its centroid	        	
        	return new double[] {g.getCentroid().getX(), g.getCentroid().getY()};	
		}
        
	    return null;
	}

	
	/**
	 * Calculate the longitude at the centroid of the geometry
	 * @param g  Input geometry
	 * @return  Longitude (in WGS84) of the centroid of the geometry
	 */
	public double getLongitude(Geometry g) {
  	
		return g.getCentroid().getX();
	}

	/**
	 * Calculate the latitude at the centroid of the geometry
	 * @param g  Input geometry
	 * @return  Latitude (in WGS84) of the centroid of the geometry
	 */
	public double getLatitude(Geometry g) {
  	
		return g.getCentroid().getY();
	}
	
	/** 
	 * Provides the internal geometry representation based on its the Well-Known Text, also applying transformation into another CRS (if required).
	 * @param wkt   WKT of the geometry
	 * @param transform    Parameters for the transformation, including source and target CRS
     * @param wktReader  Parser of WKT geometry representations
	 * @return  The transformed geometry
	 */	
	public Geometry WKT2GeometryTransform(String wkt, MathTransform transform, WKTReader wktReader) {  
	  	    
			Geometry g = null;
  	        try {
  	        	g = wktReader.read(wkt);
  	        	g = JTS.transform(g, transform);
  			} catch (Exception e) {
  				e.printStackTrace();
  			}
        
  	        return g;     //Return geometry
	}

	
	/** 
	 * Merges several input files into a single output file.
	 * @param inputFiles  List of the paths to the input files
	 * $param outputFile Path to merged output file
	 */	
	public void mergeFiles(List<String> inputFiles, String outputFile) {
		
		OutputStream out;
		InputStream in;
		try {
			out = new FileOutputStream(outputFile);
			byte[] buf = new byte[1000];
		    for (String file : inputFiles) {
		        in = new FileInputStream(file);
		        int b = 0;
		        while ( (b = in.read(buf)) >= 0) {
		            out.write(buf, 0, b);
		            out.flush();
		        }
		    }
		    out.close();
		} catch (Exception e) {
			ExceptionHandler.abort(e, "Output files were not merged.");
		}
	}



	/**
	 * Provides the next serial number (long) to be used as an intermediate identifier
	 * @return  A long number.
	 */
    public long getNextSerial() {
        return numberGenerator.getAndIncrement();
    }
    
	/**
	 * Built-in function that provides a UUID (Universally Unique Identifier) that represents a 128-bit long value to be used in the URI of a transformed feature.
     * Also known as GUID (Globally Unique Identifier).
     * @param featureSource  The name of the feature source, to be used as suffix of the identifier.
	 * @param id  A unique identifier of the feature.
	 * @return The auto-generated UUID based on the concatenation of the feature source and the identifier.
	 */
	public String getUUID(String featureSource, String id) {
			
		UUID uuid = null;

		//Auto-generate a serial number in case that no unique identifier is available for the original feature
		//CAUTION! This serial number is neither retained not emitted in the resulting triples
		if (id == null)
			id = Long.toString(getNextSerial());

		//UUIDs generated by hashing over the concatenation of feature source name and the identifier
		try {
		    byte[] bytes = (featureSource + id).getBytes("UTF-8");
			uuid = UUID.nameUUIDFromBytes(bytes);
		} catch (Exception e) {
			e.printStackTrace();
		}

		return uuid.toString();	
	}
		
	/**
	 * Built-in function that provides a UUID (Universally Unique Identifier) that represents a 128-bit long value to be used in the URI of a transformed feature.
     * This UUID is generated by hashing over the original identifier. Also known as GUID (Globally Unique Identifier).
	 * @param id  A unique identifier of the feature.
	 * @return The auto-generated UUID.
	 */
	public String getUUID(String id) {
			
		UUID uuid = null;

		try {
		    byte[] bytes = id.getBytes("UTF-8");     //UUIDs generated by hashing over the original identifier
			uuid = UUID.nameUUIDFromBytes(bytes);
		} catch (Exception e) {
			e.printStackTrace();
		}
		 
		return uuid.toString();	
	}

	/**
	 * Built-in function that provides a UUID (Universally Unique Identifier) that represents a 128-bit long value to be used in the URI of a transformed feature.
     * This is a secure random UUID with minimal chance of collisions with existing ones. Also known as GUID (Globally Unique Identifier).
	 * @return The auto-generated UUID.
	 */
	public String getRandomUUID() {		
		return UUID.randomUUID().toString();          //random UUID
	} 

	/**
	 * Build-in function that retains the original identifier of a feature in the resulting URI or the transformed resource.
	 * @param id  A unique identifier of the feature.
	 * @return   The identifier to be used for the transformed resource.
	 */
	public String keepOriginalID(String id) {
		
		return id;	
	}
	
	/**
	 * Provides a UTF-8 encoding of the given string originally represented in the given encoding
	 * @param s  input string value
	 * @param encoding  name of the character encoding
	 * @return  output encoded string
	 */
	public String encodeUTF(String s, String encoding) {
			
		byte[] ptext = s.getBytes(); //Charset.forName(encoding)); 
		String value = new String(ptext, Charset.forName("UTF-8"));
		 
		return value;
	}

	/**
	 * Checks if the given string represents a valid ISO 639-1 language code (2 digits)
	 * @param s  An input string value 
	 * @return  True is this is a valid ISO 639-1 language code; otherwise, False.
	 */
	public boolean isValidISOLanguage(String s) {
        return ISO_LANGUAGES.contains(s);
    }
	
	/**
	 * Built-in function that extracts the language tag from an attribute name. This tag will be attached to all values obtained for this attribute.
	 * ASSUMPTION: The tag is composed from the suffix after the i-th character in the attribute name.
	 * @param attr  The attribute name.
	 * @param i  Index of the i-th character in the attribute name.
	 * @return  The language tag to be applied in string literals created for values from this attribute.
	 */
	public String getLanguage(String attr, int i) {

		String lang = null;
		if (attr.length() > i)   //&& (attr.length() <= i+2)    //CAUTION! Not checking here for a valid 2-digit specification (ISO 639-1) for languages
			lang = attr.substring(i);                           //Get the suffix after the i-th character in the attribute name
		return lang;
	}
	
	/**
	 * Built-in function that identifies the provider of the dataset as specified in the configuration settings.
	 * @return  The name of the data provider.
	 */
	public String getDataSource() {
		
		return currentConfig.featureSource;	
	}


	/**
	 * Built-in function that concatenates a pair of string values into a new one.
	 * @param val1  The first value.
	 * @param val2  The second value.
	 * @return  The concatenated value.
	 */
	public String concatenate(String val1, String val2) {
		
		return (val1 + "  " + val2).trim();	
	}


	/**
	 * Built-in function that concatenates an array of multiple string values into a unified one.
	 * @param values  The array of string values.
	 * @return  The concatenated value.
	 */
	public String concatenate(String[] values) {
		
		String concat = null;
		for (String v: values) {
			concat = new StringBuilder(concat).append(v).append(" ").toString();			
		}
		return concat.trim();
	}
	
}
