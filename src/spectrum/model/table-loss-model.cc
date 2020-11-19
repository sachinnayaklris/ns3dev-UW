/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2020 University of Washington
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Authors: Tom Henderson <tomh@tomh.org>
 *          Collin Brady <collinb@uw.edu>
 */

#include <ns3/mobility-model.h>
#include <ns3/table-loss-model.h>
#include <ns3/simulator.h>
#include <ns3/node.h>
#include <iostream>
#include <sstream>
#include <fstream>
#include <string> 
#include <vector>

namespace ns3 {

NS_LOG_COMPONENT_DEFINE ("TableLossModel");

NS_OBJECT_ENSURE_REGISTERED (TableLossModel);


TableLossModel::TableLossModel ()
{
	NS_LOG_FUNCTION (this);
  	SetNext (NULL);
}

TableLossModel::~TableLossModel ()
{
}


TypeId
TableLossModel::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::TableLossModel")
    .SetParent<SpectrumPropagationLossModel> ()
    .SetGroupName ("Spectrum")
    .AddConstructor<TableLossModel> ()
  ;
  return tid;
}

Ptr<SpectrumValue>
TableLossModel::DoCalcRxPowerSpectralDensity (Ptr<const SpectrumValue> txPsd,
                                                                 Ptr<const MobilityModel> a,
                                                                 Ptr<const MobilityModel> b) const
{
  //std::cout << "*";
  Ptr<SpectrumValue> rxPsd = Copy<SpectrumValue> (txPsd);
  Values::iterator vit = rxPsd->ValuesBegin ();
  Bands::const_iterator fit = rxPsd->ConstBandsBegin ();

  NS_ASSERT (a);
  NS_ASSERT (b);


  // assume a is the eNb, b is the UE, on the DL
  uint32_t enbId = a->GetObject<Node> ()->GetId();
  uint32_t ueId = b->GetObject<Node> ()->GetId();
  uint32_t currentRb = 0;
  
  //std::cout << enbId << "\n";
  //std::cout << ueId << "\n";
  //std::cout << currentRb << "\n";
  
  while (vit != rxPsd->ValuesEnd ())
    {
      NS_ASSERT (fit != rxPsd->ConstBandsEnd ());
      *vit = GetRxPsd (enbId, ueId, currentRb);
      ++vit;
      ++fit;
      ++currentRb;
    }
  return rxPsd;
}


double
TableLossModel::GetRxPsd (uint32_t enbId, uint32_t ueId, uint32_t rbIndex) const
{
  // compute array index from 'now' which must be discretized to a 1us boundary
  //std::cout << "*";
  uint64_t nowMs = Simulator::Now ().GetMilliSeconds ();
  //std::cout << nowMs << "\n";
  //std::cout << enbId << "\n";
  //std::cout << ueId - m_numEnb << "\n";
  //std::cout << rbIndex << "\n";
  // fetch and return value for (enbId, ueId, nowUs) from data structure
  return m_traceVals[enbId][ueId - m_numEnb][rbIndex][nowMs];//the ueID variable in numbered UEID = (numeNb,...,numeNb+numUe-1) so a subtractor is needed
  
}


void
TableLossModel::initializeTraceVals (uint32_t numEnbs, uint32_t numUes, uint32_t numRbs, uint32_t simSubFrames)
{
  //std::cout << "*";
  m_numRb = numRbs;
  m_numEnb = numEnbs;
  m_numUe = numUes;
  m_numSubFrames = simSubFrames;
  
  m_traceVals.resize(numEnbs);
  for (uint32_t n = 0; n < numEnbs; ++n)
  {
    m_traceVals[n].resize(numUes);
    for (uint32_t m = 0; m < numUes; ++m)
    {
      m_traceVals[n][m].resize(numRbs);
      for (uint32_t r = 0; r < numRbs; ++r)
      {
        m_traceVals[n][m][r].resize(simSubFrames);
      }
    }
  }
}





void
TableLossModel::LoadTrace (std::string path, std::string fileName)
{
  
  // get the identifiers from the filename
  // filename bust be formatted as such: 
  //SECTION NOT DONE 
  //std::string fileName = "ULDL_Channel_Response_TX_1_Sector_1_UE_1_.txt";
  std::vector <std::string> tokens; 

  std::stringstream toParse(fileName); 
  std::string temp; 

  while(std::getline(toParse, temp, '_')) 
  { 
      tokens.push_back(temp); 
  } 

    
  int enbId = std::stoi(tokens[4]);
  int ueId  = std::stoi(tokens[8]);
  int sectorId = std::stoi(tokens[6]);
  
  
  std::ifstream  data(path + fileName);
  std::string line;
  double val;
  
  
  for (uint32_t currentRb = 0; currentRb < m_numRb; ++currentRb)
  {
      std::getline(data,line);
      std::stringstream lineStream(line);
      for (uint32_t currentTimeIndex = 0; currentTimeIndex < m_numSubFrames; ++currentTimeIndex)
      {
          lineStream >> val;
          //std::cout << "@" << std::endl;
          m_traceVals[3*(enbId-1)+(sectorId-1)][ueId-1][currentRb][currentTimeIndex] = val;

          if(lineStream.peek() == ' ') lineStream.ignore();

      }
  }
  
  
  
}

}  // namespace ns3
