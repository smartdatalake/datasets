/*
 * @(#) OsmXmlToRdf.java	version 1.8   2/5/2019
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
package eu.smartdatalake.athenarc.osmwrangle.tools;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.xml.parsers.ParserConfigurationException;
import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;

import org.geotools.factory.Hints;
import org.geotools.referencing.CRS;
import org.geotools.referencing.ReferencingFactoryFinder;
import org.opengis.referencing.crs.CRSAuthorityFactory;
import org.opengis.referencing.crs.CoordinateReferenceSystem;
import org.opengis.referencing.operation.MathTransform;
import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.helpers.DefaultHandler;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.Geometry;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.LineString;
import com.vividsolutions.jts.geom.LinearRing;
import com.vividsolutions.jts.geom.Point;
import com.vividsolutions.jts.geom.Polygon;
import com.vividsolutions.jts.geom.PrecisionModel;
import com.vividsolutions.jts.io.WKTReader;

import eu.smartdatalake.athenarc.osmwrangle.osm.OSMClassification;
import eu.smartdatalake.athenarc.osmwrangle.osm.OSMDiskIndex;
import eu.smartdatalake.athenarc.osmwrangle.osm.OSMMemoryIndex;
import eu.smartdatalake.athenarc.osmwrangle.osm.OSMNode;
import eu.smartdatalake.athenarc.osmwrangle.osm.OSMRecord;
import eu.smartdatalake.athenarc.osmwrangle.osm.OSMRecordBuilder;
import eu.smartdatalake.athenarc.osmwrangle.osm.OSMRelation;
import eu.smartdatalake.athenarc.osmwrangle.osm.OSMWay;

import eu.smartdatalake.athenarc.osmwrangle.utils.Assistant;
import eu.smartdatalake.athenarc.osmwrangle.utils.Classification;
import eu.smartdatalake.athenarc.osmwrangle.utils.Configuration;
import eu.smartdatalake.athenarc.osmwrangle.utils.ExceptionHandler;
import eu.smartdatalake.athenarc.osmwrangle.utils.OsmCsvConverter;
import eu.smartdatalake.athenarc.osmwrangle.utils.ValueChecker;


/**
 * Entry point to convert OpenStreetMap (OSM) XML files into RDF triples using Saxon XSLT.
 * LIMITATIONS: - Depending on system and JVM resources, transformation can handle only a moderate amount of OSM features in memory. 
 * @author Kostas Patroumpas
 * @version 1.8
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 19/4/2017
 * Modified: 7/9/2017; added filters for tags in order to assign categories to extracted OSM features according to a user-specified classification scheme (defined in an extra YML file).
 * Modified: 3/11/2017; added support for system exit codes on abnormal termination
 * Modified: 19/12/2017; reorganized collection of triples using TripleGenerator
 * Modified: 24/1/2018; included auto-generation of UUIDs for the URIs of features
 * Modified: 7/2/2018; added support for exporting all available non-spatial attributes as properties
 * Modified: 12/2/2018; added support for reprojection to another CRS
 * Modified: 13/2/2018; handling incomplete OSM relations in a second pass after the XML file is parsed in its entirety
 * Modified: 31/5/2018; emit RDF triples concerning the classification scheme utilized in assigning categories to OSM elements.
 * Modified: 15/6/2018; introduced a preliminary scan of OSM ways and relations in order to index referenced elements only.
 * Modified: 20/6/2018; added option for disk-based indices in order to cope with larger OSM datasets
 * Modified: 4/7/2018; reorganized identification of categories based on OSM tags
 * Modified: 27/9/2018; excluded creation of linear ring geometries for roads and barriers; polygons are created instead
 * Modified; 24/10/2018; allowing transformation to proceed even in case that no filters (using OSM tags) have been specified; no classification scheme will be used in this case.
 * Last modified by: Kostas Patroumpas, 30/4/2019
 */
public class OsmXmlToRdf extends DefaultHandler {

	  OsmCsvConverter myConverter;
	  Assistant myAssistant;
	  ValueChecker myChecker;
	  private MathTransform reproject = null;
	  int sourceSRID;                       //Source CRS according to EPSG 
	  int targetSRID;                       //Target CRS according to EPSG
	  private Configuration currentConfig;  //User-specified configuration settings
	  private String inputFile;             //Input OSM XML file
	  private String outputFile;            //Output RDF file
	
	  Classification classification = null;        //Classification hierarchy for assigning categories to features
	  
	  //Initialize a CRS factory for possible reprojections
	  private static final CRSAuthorityFactory crsFactory = ReferencingFactoryFinder
		       .getCRSAuthorityFactory("EPSG", new Hints(Hints.FORCE_LONGITUDE_FIRST_AXIS_ORDER, Boolean.TRUE));
	  
	  long numNodes;
	  long numWays;
	  long numRelations;
	  long numNamedEntities;

	  private GeometryFactory geometryFactory = new GeometryFactory();
	    
	  private OSMRecordBuilder recBuilder;				   //Creates OSM records with all spatial and thematic information extracted from OSM elements
	 
	  private Map<String, Geometry> tmpNodeIndex;     	   //Temporary dictionary for OSM node elements
	  private Map<String, Geometry> tmpWayIndex;      	   //Temporary dictionary for OSM way elements
	  private Map<String, Geometry> tmpRelationIndex; 	   //Temporary dictionary for OSM relation elements
	    
	  private OSMNode nodeTmp;                             //the current OSM node object
	  private OSMWay wayTmp;                               //the current OSM way object
	  private OSMRelation relationTmp;                     //the current OSM relation object
	    
	  private Set<String> tags;                            //OSM tags used in the filters
	  
	  private boolean inWay = false;                       //when parser is in a way node becomes true in order to track the parser position 
	  private boolean inNode = false;                      //becomes true when the parser is in a simple node        
	  private boolean inRelation = false;                  //becomes true when the parser is in a relation node
	
	  private boolean scanWays = true;                     //Activates preliminary scanning of OSM ways in order to create index structures required during parsing
	  private boolean scanRelations = true;                //Activates preliminary scanning of OSM relations in order to create index structures required during parsing
	  private boolean rescanRelations = false;             //Activates an auxiliary scan of OSM relations that may be referenced by other relations
	  private boolean keepIndexed = false;                 //Determines whether to index references of a given OSM element based on its tags; discarded if none of its tags matches with the user-specified OSM filters 

	  /**
	   * Constructor for the transformation process from OpenStreetMap XML file to RDF.
	   * @param config  Parameters to configure the transformation.
	   * @param inFile  Path to input OSM XML file.
	   * @param outFile  Path to the output file that collects RDF triples.
	   * @param sourceSRID  Spatial reference system (EPSG code) of the input OSM XML file.
	   * @param targetSRID  Spatial reference system (EPSG code) of geometries in the output RDF triples.
	   */
	  public OsmXmlToRdf(Configuration config, String inFile, String outFile, int sourceSRID, int targetSRID) {
       
		  currentConfig = config;
		  inputFile = inFile;
		  outputFile = outFile;
	      this.sourceSRID = sourceSRID;                      //Assume that OSM input is georeferenced in WGS84
	      this.targetSRID = targetSRID;
	      myAssistant = new Assistant();
	      myChecker = new ValueChecker();
	      
	      //Get filter definitions over combinations of OSM tags in order to determine POI categories
	      try {
	    	  OSMClassification osmClassific = new OSMClassification(null, currentConfig.outputDir);
	    	  String classFile = osmClassific.apply();
	    	  tags = osmClassific.getTags();
	    	  
		      //Instantiate a record builder to be used in handling each OSM record
		      recBuilder = new OSMRecordBuilder(osmClassific.getFilters());
		     
		      //Create the internal representation of this classification scheme
		      if (tags != null) 
		      {
		    	  String outClassificationFile = currentConfig.outputDir + "categories.csv";
		    	  classification = new Classification(classFile, outClassificationFile);
		      }
		      
	      }
		  catch(Exception e) { 
				ExceptionHandler.abort(e, "Cannot initialize parser for OSM data. Missing or malformed YML file with classification of OSM tags into categories.");
		  }

	      //Check if a coordinate transform is required for geometries
	      if (currentConfig.targetCRS != null)
	      {
	  	    try {
	  	        boolean lenient = true; // allow for some error due to different datums
	  	        CoordinateReferenceSystem sourceCRS = crsFactory.createCoordinateReferenceSystem(currentConfig.sourceCRS);
	  	        CoordinateReferenceSystem targetCRS = crsFactory.createCoordinateReferenceSystem(currentConfig.targetCRS);    
	  	        reproject = CRS.findMathTransform(sourceCRS, targetCRS, lenient);
	  	        
	  	        //Needed for parsing original geometry in WTK representation
	  	        GeometryFactory geomFactory = new GeometryFactory(new PrecisionModel(), sourceSRID);
	  	        myAssistant.wktReader = new WKTReader(geomFactory);
	  	        
	  		} catch (Exception e) {
	  			ExceptionHandler.abort(e, "Error in CRS transformation (reprojection) of geometries.");      //Execution terminated abnormally
	  		}
	      }
	      else                                 //No transformation specified; determine the CRS of geometries...
	    	  this.targetSRID = 4326;          //... as the original OSM features assumed in WGS84 lon/lat coordinates
		    
	  }

		

	  /**
	   * Calls Saxon transformation to parse the input XML file.
	   */
	  public void parseDocument() {
		    //Depending of input file size, determine if indices will be kept in-memory of will be disk-based
	    	File inFile = new File(inputFile);
	    	if (inFile.length() < 0.5 * Runtime.getRuntime().maxMemory() ) {          //CAUTION! Rule of thumb: Input XML file size is less than half of the JVM heap size, so memory is expected to be sufficient for indexing OSM elements    
		    	//OPTION #1: Memory-based native Java structures for indexing
	    		recBuilder.nodeIndex = new OSMMemoryIndex(); 
	    		recBuilder.wayIndex = new OSMMemoryIndex();
	    		recBuilder.relationIndex = new OSMMemoryIndex();
		        System.out.println("Buidling in-memory indices over OSM elements...");
	    	}
	    	else {                                               //For larger OSM files, resort to disk-based indexing of their referenced elements
		    	//OPTION #2: Disk-based structures for indexing
	    		recBuilder.nodeIndex = new OSMDiskIndex(currentConfig.tmpDir, "nodeIndex");
	    		recBuilder.wayIndex = new OSMDiskIndex(currentConfig.tmpDir, "wayIndex");
	    		recBuilder.relationIndex = new OSMDiskIndex(currentConfig.tmpDir, "relationIndex");
		        System.out.println("Buidling disk-based indices over OSM elements...");
	    	}
	    	
	    	//This list will hold OSM relations that depend on other relations, so these must be checked once the entire OSM file is exhausted.
	    	recBuilder.incompleteRelations = new ArrayList<>();
	        
	        //Invoke XSL transformation against input OSM XML file
	        System.out.println("Calling parser for OSM XML file...");
	        SAXParserFactory factory = SAXParserFactory.newInstance();
	        try {
	        	//Preliminary INDEXING phase: first scan of OSM relations to build the required index structures
	        	scanRelations = true;
	        	scanWays = false;
	        	keepIndexed = false;
		    	tmpNodeIndex = new HashMap<>();          //These temporary containers are used to hold references for each OSM element examined; they MUST be purged before the next element is examined
		        tmpWayIndex = new HashMap<>();
		        tmpRelationIndex = new HashMap<>();
	        	System.out.println("Scanning OSM relations to identify indexed OSM elements...");
	            SAXParser parser = factory.newSAXParser();
	            parser.parse(inputFile, this);
	            parser.reset();
	            System.out.println("Indexed " + recBuilder.nodeIndex.size() + " nodes, " + recBuilder.wayIndex.size() + " ways, and " + recBuilder.relationIndex.size() + " relations.");
	            
	            if (rescanRelations) {
		            //Preliminary INDEXING phase: second scan of OSM relations to build the required index structures, since relations may refer to other relations
		        	scanRelations = true;
		        	scanWays = false;
		        	keepIndexed = false;
			    	tmpNodeIndex = new HashMap<>();          //These temporary containers are used to hold references for each OSM element examined; they MUST be purged before the next element is examined
			        tmpWayIndex = new HashMap<>();
			        tmpRelationIndex = new HashMap<>();
		        	System.out.println("Second scan of OSM relations to identify other referenced OSM relations...");
		            parser = factory.newSAXParser();
		            parser.parse(inputFile, this);
		            parser.reset();
		            System.out.println("Indexed " + recBuilder.nodeIndex.size() + " nodes, " + recBuilder.wayIndex.size() + " ways, and " + recBuilder.relationIndex.size() + " relations.");
	            }
	            
	            //Preliminary INDEXING phase: only scan OSM ways to build the required index structures
	        	scanWays = true;
	        	scanRelations = false;
	        	keepIndexed = false;
		    	tmpNodeIndex = new HashMap<>();          //These temporary containers are used to hold references for each OSM element examined; they MUST be purged before the next element is examined
		        tmpWayIndex = new HashMap<>();
		        tmpRelationIndex = new HashMap<>();
	        	System.out.println("Scanning OSM ways to identify indexed OSM elements...");
	            parser = factory.newSAXParser();
	            parser.parse(inputFile, this);
	            parser.reset();
	            System.out.println("Indexed " + recBuilder.nodeIndex.size() + " nodes, " + recBuilder.wayIndex.size() + " ways, and " + recBuilder.relationIndex.size() + " relations.");
            
//	            System.out.println("NODES:");
//	            nodeIndex.print();
//	            System.out.println("WAYS:");
//	            wayIndex.print();
//	            System.out.println("RELATIONS:");
//	            relationIndex.print();
	            
	            //PARSING phase: Take advantage of precomputed indices when parsing
	            scanRelations = false;
	            scanWays = false;
	            System.out.println("Starting parsing of all OSM elements...");
	            parser = factory.newSAXParser();
	            parser.parse(inputFile, this);
	            parser.reset();
	            
	            //Second pass over incomplete OSM relations, once the entire XML file has been parsed
	            for (Iterator<OSMRelation> iterator = recBuilder.incompleteRelations.iterator(); iterator.hasNext(); )
	            {
	            	OSMRelation r = iterator.next();
//	            	System.out.print("Re-examining OSM relation " + r.getID() + "...");
	            	OSMRecord rec = recBuilder.createOSMRecord(r);
	            	if (rec != null)                    //Incomplete relations are accepted in this second pass, consisting of their recognized parts   
	            	{
	            		if (r.getTagKeyValue().containsKey("name"))
	            		{
	            			myConverter.parse(myAssistant, rec, classification, reproject, targetSRID);
	            			numNamedEntities++;
	            		}
	            		//Keep this relation geometry in the dictionary, just in case it might be referenced by other OSM relations
	            		if (recBuilder.relationIndex.containsKey(r.getID().substring(1, r.getID().length()-1)))
	            			recBuilder.relationIndex.put(r.getID().substring(1, r.getID().length()-1), rec.getGeometry()); 
	            		numRelations++;
	            		iterator.remove();                                              //This OSM relation should not be examined again
//	            		System.out.println("Done!");
	            	} 
	            	else
	            		System.out.println(" Transformation failed!");
	            }
	            
	            System.out.println("\nFinished parsing OSM relations.");
	            recBuilder.nodeIndex.clear();											//Discard index over OSM nodes			
	            recBuilder.wayIndex.clear();                                      		//Discard index over OSM ways
	            recBuilder.relationIndex.clear();                                       //Discard index over OSM relations
	            
	        } catch (ParserConfigurationException e) {
	        	ExceptionHandler.abort(e, "Parser Configuration error.");
	        } catch (SAXException e) {
	        	ExceptionHandler.abort(e, "SAXException : OSM xml not well formed." );
	        } catch (IOException e) {
	        	ExceptionHandler.abort(e, "Cannot access input file.");
	        }
	        
	    }

	    /**
	     * Starts parsing of a new OSM element (node, way, or relation). Overrides method in parent Saxon class to initialize variables at the start of parsing of each OSM element.
	     * @param s  The Namespace URI, or the empty string if the element has no Namespace URI or if Namespace processing is not being performed.
	     * @param s1  The local name (without prefix), or the empty string if Namespace processing is not being performed.
	     * @param elementName  The qualified name (with prefix), or the empty string if qualified names are not available.
	     * @param attributes   The attributes attached to the element. If there are no attributes, it shall be an empty Attributes object.
	     */
	    @Override
	    public void startElement(String s, String s1, String elementName, Attributes attributes) throws SAXException {
	    
	    	try {
		        //Depending on the name of the current OSM element,... 
		        if ((!scanWays) && (!scanRelations) && (elementName.equalsIgnoreCase("node"))) {           //Create a new OSM node object and populate it with the appropriate values
		            nodeTmp = new OSMNode();
		            nodeTmp.setID(attributes.getValue("id"));
	
		            //Parse geometry
		            double longitude = Double.parseDouble(attributes.getValue("lon"));
		            double latitude = Double.parseDouble(attributes.getValue("lat"));
		           
		            //Create geometry object with original WGS84 coordinates
		            Geometry geom = geometryFactory.createPoint(new Coordinate(longitude, latitude));
		            nodeTmp.setGeometry(geom);
		            inNode = true;
		            inWay = false;
		            inRelation = false;
		        } 
		        else if ((!scanRelations) && (elementName.equalsIgnoreCase("way"))) {       //Create a new OSM way object and populate it with the appropriate values
		            wayTmp = new OSMWay();
		            wayTmp.setID(attributes.getValue("id"));
		            
        			if ((scanWays) && (recBuilder.wayIndex.containsKey(wayTmp.getID())))    //This OSM way is referenced by a relation, so its nodes should be kept in the index
        				keepIndexed = true;	        			
        			
		            if ((!scanWays) && (!scanRelations)) {
			            if (inNode)
			            	System.out.println("\nFinished parsing OSM nodes.");
			            
			            inWay = true;
			            inNode = false;
			            inRelation = false;
		            }
		        } 
		        else if ((!scanWays) && (elementName.equalsIgnoreCase("relation"))) {   //Create a new OSM relation and populate it with the appropriate values
		            relationTmp = new OSMRelation();
		            relationTmp.setID(attributes.getValue("id"));
		            
        			if (recBuilder.relationIndex.containsKey(relationTmp.getID()))
	        			keepIndexed = true;
        			
        			if ((!scanWays) && (!scanRelations)) {
			            if (inWay)
			            	System.out.println("\nFinished parsing OSM ways.");
			            
			            inRelation = true;
			            inWay = false;
			            inNode = false;
        			}
		        } 
		        else if (elementName.equalsIgnoreCase("nd")) {
		        	if ((scanWays) || (scanRelations)) {
		        		tmpNodeIndex.put(attributes.getValue("ref"), null);                 //This node is referenced by a way; keep it in the index, and its geometry will be filled in when parsing the nodes 
		        	} else
		        		wayTmp.addNodeReference(attributes.getValue("ref"));
		        } 
		        else if (elementName.equalsIgnoreCase("tag")) {
		        	if ((scanWays) || (scanRelations))	{                     	//In preliminary phase, if no tag of this OSM element is included in the OSM filters, no references need be indexed
	        			if ((tags == null) || (tags.contains(attributes.getValue("k"))))       		//CAUTION! Filter out any OSM elements not related to tags specified by the user
	        				keepIndexed = true;                                                     //In case of no tags specified for filtering, index all OSM elements
		        	}
		        	else {                                                                  //In the parsing phase, keep all tags for that OSM element
			            if (inNode) {
			                //If the path is in an OSM node, then set tagKey and value to the corresponding node     
			                nodeTmp.setTagKeyValue(attributes.getValue("k"), myChecker.removeIllegalChars(attributes.getValue("v")));
			            } 
			            else if (inWay) {
			                //Otherwise, if the path is in an OSM way, then set tagKey and value to the corresponding way
			                wayTmp.setTagKeyValue(attributes.getValue("k"), myChecker.removeIllegalChars(attributes.getValue("v")));
			            } 
			            else if(inRelation){
			                //Set the key-value pairs of OSM relation tags
			                relationTmp.setTagKeyValue(attributes.getValue("k"), myChecker.removeIllegalChars(attributes.getValue("v")));
			            }
		        	}
		        } 
		        else if (elementName.equalsIgnoreCase("member")) {
		        	if ((scanRelations) || (scanWays)) {
		        		if (attributes.getValue("type").equalsIgnoreCase("node"))
		        			tmpNodeIndex.put(attributes.getValue("ref"), null);                //This node is referenced by a relation; keep it in the index, and its geometry will be filled in when parsing the nodes
		        		else if (attributes.getValue("type").equalsIgnoreCase("way"))
		        			tmpWayIndex.put(attributes.getValue("ref"), null);                 //This way is referenced by a relation; keep it in the index, and its geometry will be filled in when parsing the ways
		        		else if (attributes.getValue("type").equalsIgnoreCase("relation"))
		        			tmpRelationIndex.put(attributes.getValue("ref"), null);            //This relation is referenced by another relation; keep it in the index, and its geometry will be filled in when parsing the relations
		        	}
		        	else
		        		relationTmp.addMemberReference(attributes.getValue("ref"), attributes.getValue("type"), attributes.getValue("role"));
		        }  
	    	}
	    	catch (Exception e) {
//	    		System.out.println(attributes.toString());
	        	ExceptionHandler.warn(e, "(START) Cannot process OSM element.");	        	
	        }    	
	    }

	    /**
	     * Concludes processing of an OSM element (node, way, or relation) once it has been parsed completely. Overrides method in the parent Saxon class to finalize variables and indices at the end of parsing of each OSM element.
	     * @param s  The Namespace URI, or the empty string if the element has no Namespace URI or if Namespace processing is not being performed.
	     * @param sl  The local name (without prefix), or the empty string if Namespace processing is not being performed.
	     * @param element   The qualified name (with prefix), or the empty string if qualified names are not available.
	     */
	    @Override
	    public void endElement(String s, String s1, String element) {
	    	
	    	try
	    	{
		        //If end of node element, add to appropriate list
		        if ((!scanWays) && (!scanRelations) && (element.equalsIgnoreCase("node"))) {    //OSM node need not be parsed during the INDEXING phase
		            if (nodeTmp.getTagKeyValue().containsKey("name"))
		            {
		            	myConverter.parse(myAssistant, recBuilder.createOSMRecord(nodeTmp), classification, reproject, targetSRID);
		            	numNamedEntities++;
		            }
		            if (recBuilder.nodeIndex.containsKey(nodeTmp.getID()))
		            	recBuilder.nodeIndex.put(nodeTmp.getID(), nodeTmp.getGeometry());         //Keep a dictionary of node geometries, only if referenced by OSM ways
		            numNodes++;
		            nodeTmp = null;
		        } 
		        else if ((!scanRelations) && (element.equalsIgnoreCase("way"))) {                  //OSM way      
		        	if (scanWays) {
		        		if ((keepIndexed) || (recBuilder.wayIndex.containsKey(wayTmp.getID())))    //Keep those nodes in the global index 
		        			recBuilder.nodeIndex.putAll(tmpNodeIndex);
		        		tmpNodeIndex.clear();                       //Clear temporary buffer and ...
		        		keepIndexed = false;                        //... reset flag for the next element
		        	}
		        	else {
			            //construct the Way geometry from each node of the node references
			            List<String> references = wayTmp.getNodeReferences();
		
			            for (String entry: references) {
			            	if (recBuilder.nodeIndex.containsKey(entry))
			            	{
			            		Geometry geometry = recBuilder.nodeIndex.get(entry);     //get the geometry of the node with ID=entry
			            		wayTmp.addNodeGeometry(geometry);             //add the node geometry in this way  
			            	}
			            	else
			            		System.out.println("Missing node " + entry + " in referencing way " + wayTmp.getID());
			            }
			            Geometry geom = geometryFactory.buildGeometry(wayTmp.getNodeGeometries());

			            //Check if the beginning and ending node are the same and the number of nodes are more than 3. 
			            //These nodes must be more than 3, because JTS does not allow construction of a linear ring with less than 3 points
			            if((wayTmp.getNodeGeometries().size() > 3) && wayTmp.getNodeGeometries().get(0).equals(wayTmp.getNodeGeometries().get(wayTmp.getNodeGeometries().size()-1)))
			            { 
				               //Always construct a polygon when a linear ring is detected
				               LinearRing linear = geometryFactory.createLinearRing(geom.getCoordinates());
				               Polygon poly = new Polygon(linear, null, geometryFactory);
				               wayTmp.setGeometry(poly);  
				            	
				               /*************************************************
				               //OPTION NOT USED: Construct a linear ring geometry when this feature is either a barrier or a road
				               if (!((wayTmp.getTagKeyValue().containsKey("barrier")) || wayTmp.getTagKeyValue().containsKey("highway"))){
				            	   //this is not a barrier nor a road, so construct a polygon geometry
				               
				            	   LinearRing linear = geometryFactory.createLinearRing(geom.getCoordinates());
				            	   Polygon poly = new Polygon(linear, null, geometryFactory);
				            	   wayTmp.setGeometry(poly);               
				               }
				               else {    //it is either a barrier or a road, so construct a linear ring geometry 
				                  LinearRing linear = geometryFactory.createLinearRing(geom.getCoordinates());
				                  wayTmp.setGeometry(linear);  
				               }
				               **************************************************/
			            }
			            else if (wayTmp.getNodeGeometries().size() > 1) {
			            //it is an open geometry with more than one nodes, make it linestring 
			                
			                LineString lineString =  geometryFactory.createLineString(geom.getCoordinates());
			                wayTmp.setGeometry(lineString);               
			            }
			            else {     //we assume that any other geometries are points
			                       //some ways happen to have only one point. Construct a Point.
			                Point point = geometryFactory.createPoint(geom.getCoordinate());
			                wayTmp.setGeometry(point);
			            }
			            
			            //CAUTION! Only named entities will be transformed
			            if (wayTmp.getTagKeyValue().containsKey("name"))  
			            {
			            	myConverter.parse(myAssistant, recBuilder.createOSMRecord(wayTmp), classification, reproject, targetSRID);
			            	numNamedEntities++;
			            }
			            
			            if (recBuilder.wayIndex.containsKey(wayTmp.getID()))
			            	recBuilder.wayIndex.put(wayTmp.getID(), wayTmp.getGeometry());          //Keep a dictionary of way geometries, only for those referenced by OSM relations
			            numWays++;
			            wayTmp = null;
			        }
		        } 	   
		        else if ((!scanWays) && (element.equalsIgnoreCase("relation"))) {                 //OSM relation
		        	if (scanRelations) {
		        		if (keepIndexed) {
		        			recBuilder.nodeIndex.putAll(tmpNodeIndex);             //Keep those nodes in the respective global index    
		        			recBuilder.wayIndex.putAll(tmpWayIndex);               //Keep those ways in the respective global index    
		        			recBuilder.relationIndex.putAll(tmpRelationIndex);     //Keep those relations in the respective global index 
		        			if (!tmpRelationIndex.isEmpty())
		        				rescanRelations = true;                            //Relations need to be scanned once more, as they may reference other relations
		        		}
		        		tmpNodeIndex.clear();                    //Clear all temporary buffers ...
		        		tmpWayIndex.clear();	        		              
		        		tmpRelationIndex.clear();
		        		keepIndexed = false;                     //... and reset flag for the next element
		        	} 
		        	else {
			        	OSMRecord rec = recBuilder.createOSMRecord(relationTmp);
			        	if (rec!= null)                  //No records created for incomplete relations during the first pass
			        	{
			        		if (relationTmp.getTagKeyValue().containsKey("name"))
			        		{
			        			myConverter.parse(myAssistant, rec, classification, reproject, targetSRID);
			        			numNamedEntities++;
			        		}
			        		
			        		if (recBuilder.relationIndex.containsKey(relationTmp.getID()))
			        			recBuilder.relationIndex.put(relationTmp.getID(), rec.getGeometry());    //Keep a dictionary of relation geometries, only for those referenced by other OSM relations

			        		numRelations++;
			        	}
			        }
		        	relationTmp = null;
		        }
	    	}
	    	catch (Exception e) {
//	    		System.out.println("Element: " + element);
	        	ExceptionHandler.warn(e, "(END) Cannot process OSM element.");
	        }
	    }

  
	/**
	 * Applies transformation according to the configuration settings.
	 */
	public void apply() {

	  numNodes = 0;
	  numWays = 0;
	  numRelations = 0;
	  numNamedEntities = 0;
        
      try {			
		  //Mode STREAM: consume entities and streamline them into a CSV file
		  myConverter =  new OsmCsvConverter(currentConfig, outputFile);
	  
		  //Parse each OSM entity and streamline the resulting triples (including geometric and non-spatial attributes)
		  parseDocument();
		  
		  //Finalize the output file
		  myConverter.store(myAssistant, outputFile);			
      } catch (Exception e) {
    	  ExceptionHandler.abort(e, "");
  	  }

      System.out.println(myAssistant.getGMTime() + " Original OSM file contains: " + numNodes + " nodes, " + numWays + " ways, " + numRelations + " relations. In total, " + numNamedEntities + " entities had a name and only those were given as input to transformation.");      
	}
	 
  
}
