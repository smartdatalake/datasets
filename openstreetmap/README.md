<html>
<HEAD>
</head>
<body>

<div id="readme" class="clearfix announce instapaper_body md">
<article class="markdown-body entry-content" itemprop="mainContentOfPage">

<h2><a name="welcome-to-osmwrangle" class="anchor" href="#welcome-to-osmwrangle"><span class="octicon octicon-link"></span></a>Welcome to OSMWrangle: An open-source tool for transforming geospatial features from OpenStreetMap into CSV files</h2>

<p>OSMWrangle is a utility developed by the <a href="http://www.imis.athena-innovation.gr/">Information Management Systems Institute</a> at <a href="http://www.athena-innovation.gr/en.html">Athena Research Center</a> under the EU/H2020 Research Project <a href="https://smartdatalake.eu/">SmartDataLake: Sustainable Data Lakes for Extreme-Scale Analytics</a>. This generic-purpose, open-source tool can be used for extracting features from <a href="https://www.openstreetmap.org/">OpenStreetMap</a> files and transforming them into records in a delimited CSV file.</p>

<p>OSMWrangle draws much of its functionality from the source code of <a href="https://github.com/SLIPO-EU/TripleGeo">TripleGeo</a>, an Extract-Transform-Load tool developed in the context of the EU/H2020 Innovation Action <a href="http://slipo.eu">SLIPO: Scalable Linking and Integration of big POI data</a>. TripleGeo extracts spatial features and their thematic attributes from a variety of geographical files and spatial DBMSs and transforms them into RDF triples.</p>

<h2>
<a name="quick-start" class="anchor" href="#Quick start"><span class="octicon octicon-link"></span></a>Quick start</h2>

<h3>
<a name="installation" class="anchor" href="#Installation"><span class="octicon octicon-link"></span></a>Installation</h3>

<ul>
<li>OSMWrangle is a command-line utility and has several dependencies on open-source and third-party, freely redistributable libraries. The <code>pom.xml</code> file contains the project's configuration in Maven.</li>
<li>
Building the application with maven:<br/>
<code>mvn clean package</code><br/>
results into a <code>osmwrangle-1.8-SNAPSHOT.jar</code> under directory <code>target</code> according to what has been specified in the <code>pom.xml</code> file.
</li>
</ul>


<h3>
<a name="execution" class="anchor" href="#Execution"><span class="octicon octicon-link"></span></a>Execution</h3>

<p>OSMWrangle supports transformation of geospatial features from two file formats (namely, XML and PBF) widely used for storing OpenStreetMap data. <a href="https://github.com/smartdatalake/datasets/tree/master/openstreetmap/test/data/">Sample OSM datasets</a> for testing are available in both file formats.</p>

<p>OSMWrangle also supports <i>classification</i> of input features into categories. In the current version, such classification is available for data regarding Points of Interest (POI), according to a two-tier <i>classification scheme</i> that describe possible amenities for Points of Interest. </p>

<p>Indicative configuration files for both OpenStreetMap formats are available <a href="https://github.com/smartdatalake/datasets/tree/master/openstreetmap/test/conf/">here</a> in order to assist you when preparing your own.</p>

<p>In addition, a custom classification scheme for POIs in OpenStreetMap data is available <a href="https://github.com/smartdatalake/datasets/tree/master/openstreetmap/src/resources/filters.yml">here</a> and can be readily used against the <a href="https://github.com/smartdatalake/datasets/tree/master/openstreetmap/test/data/">sample datasets</a>. </p>

<p>In execution, depending on the input data size you should allocate enough memory to JVM (with the <code>-Xmx</code> directive) in order to boost performance; otherwise, OSMWrangle would rely on disk-based indexing and may run less efficiently. </p>

<ul>
<li>Assuming that input OpenStreetMap data are contained in an <b>XML file</b> (i.e., file has .osm extension) as specified in the user-defined configuration file in <code>./test/conf/OSM_XML_options.conf</code>, and assuming that binaries are bundled together in <code>/target/osmwrangle-1.8-SNAPSHOT.jar</code>, give a command like this:</br>
<code>java -Xmx2g -cp ./target/osmwrangle-1.8-SNAPSHOT.jar eu.smartdatalake.athenarc.osmwrangle.Extractor ./test/conf/OSM_XML_options.conf</code></li>

<li>In case that input OpenStreetMap data are contained in an <b>PBF file</b> (i.e., file has .osm.pbf extension) as specified in the user-defined configuration file in <code>./test/conf/OSM_PBF_options.conf</code>, and assuming that binaries are bundled together in <code>/target/osmwrangle-1.8-SNAPSHOT.jar</code>, give a command like this:</br>
<code>java -Xmx2g -cp ./target/osmwrangle-1.8-SNAPSHOT.jar eu.smartdatalake.athenarc.osmwrangle.Extractor ./test/conf/OSM_PBF_options.conf</code></li>
</ul>

<p>Wait until the process gets finished, and verify that the resulting output files are according to your specifications.</p>

<p><b> NOTE: </b> All execution commands and configurations refer to the current version (OSMWrangle ver. 1.8).</p>


<h2>
<a name="license" class="anchor" href="#license"><span class="octicon octicon-link"></span></a>License</h2>

<p>The contents of this project are licensed under the <a href="https://github.com/smartdatalake/datasets/blob/master/openstreetmap/LICENSE">GPL v3 License</a>.</p></article>

</body>
</html>
