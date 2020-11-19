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
 */

#ifndef TABLE_LOSS_MODEL_H
#define TABLE_LOSS_MODEL_H


#include <ns3/object.h>
#include <ns3/mobility-model.h>
#include <ns3/spectrum-value.h>
#include <ns3/spectrum-propagation-loss-model.h>


namespace ns3 {

/**
 * \ingroup spectrum
 *
 * \brief Table-based spectrum propagation loss model
 *
 */
class TableLossModel : public SpectrumPropagationLossModel
{
public:
  TableLossModel ();
  virtual ~TableLossModel ();

  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId ();
  
  /*
   * loads the trace into memory
  */
  void LoadTrace (std::string path, std::string fileName);
  
  /*
   * initializes the size of the traceVals variable so data can be loaded correctly
  */
  void initializeTraceVals (uint32_t numeNbs, uint32_t numUes, uint32_t numRbs, uint32_t simSubFrames);

private:
  // Documented in base class
  virtual Ptr<SpectrumValue> DoCalcRxPowerSpectralDensity (Ptr<const SpectrumValue> txPsd,
                                                           Ptr<const MobilityModel> a,
                                                           Ptr<const MobilityModel> b) const;
  
  
  
  
  
  /*
   * grabs the specific value from memory to place into the spectrum value object in DoCalcRxPowerSpectralDensity
  */
  double GetRxPsd (uint32_t ueId, uint32_t enbID, uint32_t currentRb) const;


  




std::string m_traceFile; //filename
std::vector<std::vector<std::vector<std::vector<double>>>> m_traceVals; //values in the traces, 4 indexes, (n,m,i,j) = (eNbID,UEID,RB#,timeIndex)
uint32_t m_numRb; ///< RB number
uint32_t m_numEnb; //number of eNb in the simulation
uint32_t m_numUe; //number of UE in the simulation
uint32_t m_numSubFrames; //number of subframes in the simulation



};

} // namespace ns3

#endif /* TABLE_LOSS_MODEL_H */
